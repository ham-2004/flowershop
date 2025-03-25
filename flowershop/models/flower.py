from odoo import models, fields, api

class FlowerFlower(models.Model):
    _name = 'flower.flower'
    _description = 'Flower'

    common_name = fields.Char(string='Common Name')
    scientific_name = fields.Char(string='Scientific Name')
    season_start = fields.Date(string='Start')
    season_end = fields.Date(string='End')
    watering_frequency = fields.Integer(help="Frequency is in number of days")
    watering_amount = fields.Float("ml")

    @api.depends('common_name', 'scientific_name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.scientific_name} ({record.common_name})"