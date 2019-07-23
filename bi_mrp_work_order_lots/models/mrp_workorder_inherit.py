# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    lot_id = fields.Many2one('stock.production.lot', readonly=False, related=False, compute='get_component_lot_value', )

    @api.onchange('lot_id', 'qty_producing')
    def change_component_lot_qty(self):
        for work_order in self:
            product_lots = self.env['stock.production.lot'].search(
                [('product_id', '=', work_order.component_id.id)])
            product_move_object = work_order.move_raw_ids.filtered(
                lambda
                    stock_move: stock_move.product_id == work_order.component_id)

            lot_product_move_line_object = product_move_object.move_line_ids.filtered(
                lambda
                    stock_move_line: stock_move_line.lot_id == work_order.lot_id and stock_move_line.product_qty > 0)

            lot_qty = lot_product_move_line_object.product_qty

            if lot_qty <= 0:
                lot_location_qty_available = work_order.component_id.with_context(
                    location=work_order.production_id.location_src_id.id, lot_id=work_order.lot_id.id).qty_available
                lot_qty = lot_location_qty_available

            if lot_qty > work_order.component_remaining_qty:
                work_order.qty_done = work_order.component_remaining_qty

    @api.depends('component_id')
    def get_component_lot_value(self):
        for work_order in self:
            product_lots = self.env['stock.production.lot'].search(
                [('product_id', '=', work_order.component_id.id)])
            product_move_object = work_order.move_raw_ids.filtered(
                lambda stock_move: stock_move.product_id == work_order.component_id)
            move_product_lot_ids = product_move_object.move_line_ids.mapped('lot_id')
            active_product_lot_ids = work_order.active_move_line_ids.filtered(
                lambda stock_move_line: stock_move_line.product_id == work_order.component_id).mapped('lot_id')
            diff_lot_ids = [lot for lot in move_product_lot_ids if lot not in active_product_lot_ids]

            if len(diff_lot_ids):
                work_order.lot_id = diff_lot_ids[0]
                lot_product_move_line_object = product_move_object.move_line_ids.filtered(
                    lambda stock_move_line: stock_move_line.lot_id == diff_lot_ids[
                        0] and stock_move_line.product_qty > 0)

                if lot_product_move_line_object.product_qty > work_order.component_remaining_qty:
                    work_order.qty_done = work_order.component_remaining_qty
                else:
                    work_order.qty_done = lot_product_move_line_object.product_qty
            else:
                product_lot_objects = self.env['stock.production.lot'].search(
                    [('product_id', '=', work_order.component_id.id)])
                product_lot_ids = [lot.id for lot in product_lot_objects if lot.product_qty > 0]
                if product_lot_ids:
                    work_order.lot_id = product_lot_ids[0]
