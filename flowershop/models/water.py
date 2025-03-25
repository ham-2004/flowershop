from collections import defaultdict
from odoo import models, fields, api

class WateringTimes(models.Model):
    _name = "flower.water"
    _description = "Flower Watering Time"
    _order = "date"

    serial_id = fields.Many2one("stock.lot", string="Flower Serial", required=True)
    date = fields.Date(string="Watering Date", default=fields.Date.today)


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    watering_frequency = fields.Integer(string="Watering Frequency (Days)", default=3, required=True)
    last_watering_date = fields.Datetime(string="Last Watered On", readonly=True)
    water_ids = fields.One2many("flower.water", "serial_id")
    is_flower = fields.Boolean("Is Flower", related="product_id.is_flower", store=True)

    def action_water_flower(self):
        flowers = self.filtered(lambda rec: rec.is_flower)
        for record in flowers:
            if record.water_ids:
                last_watered_date = record.water_ids[0].date
                frequency = record.product_id.flower_id.watering_frequency
                today = fields.Date.today()
                if (today - last_watered_date).days < frequency:
                    continue
            self.env["flower.water"].create({
                "serial_id": record.id,
            })

    def action_open_watering_times(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "flower.water",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [["serial_id", "=", self.id]],
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product = self.env["product.product"].browse(vals["product_id"])
            if product.sequence_id:
                vals["name"] = product.sequence_id.next_by_id()
        return super().create(vals_list)
