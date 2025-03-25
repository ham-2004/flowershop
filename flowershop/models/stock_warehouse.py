from http.client import responses

from odoo import models, fields, api, _
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)

class StockWarehouseWeather(models.Model):
    _name = 'stock.warehouse.weather'
    _description = 'Stock Warehouse Weather'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, ondelete="cascade")

    temperature = fields.Float(string='Temperature (°C)', required=True)
    pressure = fields.Float(string='Pressure (hPa)', required=True)
    humidity = fields.Float(string='Humidity (%)', required=True)
    wind_speed = fields.Float(string='Wind Speed (m/s)', required=True)
    rain_volume = fields.Float("Rain Volume (mm)", help="Rain volume for the past hour")
    description = fields.Text(string='Weather Description', required=True)
    capture_time = fields.Datetime("Captured At", default=fields.Datetime.now)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    partner_id = fields.Many2one('res.partner', string="Warehouse Location", compute="_compute_partner", store=True)

    @api.depends('company_id.partner_id')
    def _compute_partner(self):
        for warehouse in self:
            warehouse.partner_id = warehouse.company_id.partner_id

    def _get_api_key_and_location(self, show_error=True):
        api_key = self.env['ir.config_parameter'].sudo().get_param('flowershop.weather_api_key')
        if api_key == 'unset' or not api_key:
            if show_error:
                _logger.warning("Weather API key is not set. Please set it in System Parameters.")
            return False, False, False

        if not self.partner_id or not self.partner_id.partner_latitude or not self.partner_id.partner_latitude:
            if show_error:
                _logger.warning(f"Warehouse {self.name} does not have a location set. Please set it in the warehouse form.")
            return False, False, False

        return api_key, self.partner_id.partner_latitude, self.partner_id.partner_longitude

    def get_weather(self, show_error=True):
        self.ensure_one()
        api_key, lat, lng = self._get_api_key_and_location(show_error)
        url = "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}".format(lat, lng, api_key)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            entries = response.json()
            self.env['stock.warehouse.weather'].create({
                "warehouse_id": self.id,
                "description": entries['weather'][0]['description'],
                "pressure": entries['main']['pressure'],
                "temperature": entries['main']['temp'],
                "humidity": entries['main']['humidity'] / 100,
                "wind_speed": entries['wind']['speed'],
                "rain_volume": entries['rain']['1h'] if 'rain' in entries else 0,
                "capture_time": datetime.now()
            })
        except Exception as e:
            _logger.error(f"Weather API call failed for {self.name}: {e}")
            if show_error:
                raise Warning(_("Could not retrieve weather data."))

    def get_weather_all_warehouses(self):
        for warehouse in self.search([]):
            warehouse.get_weather(show_error=False)

    def get_forecast_all_warehouses(self, show_error=True):
        flower_serials_to_water = self.env["stock.lot"]
        for warehouse in self:
            api_key, lat, lng = warehouse._get_api_key_and_location(show_error)
            url = "https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid={}".format(lat, lng, api_key)
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                entries = response.json()

                for i in range(0, 4):
                    if "rain" in entries["list"][i]:
                        rain = entries["list"][i]["rain"]["3h"]
                        if rain > 0.2:
                            is_rainy_today = True
                            break
                if is_rainy_today:
                    flower_products = self.env["product.product"].search([("is_flower", "=", True)])
                    quants = self.env["stock_quant"].search([
                        ("product_id", "in", flower_products.ids),
                        ("location_id", "=", warehouse.lot_stock_id.id)
                    ])
                    flower_serials_to_water |= quants.mapped("lot_id")
            except Exception as e:
                _logger.error(f"Forecast API call failed for {warehouse.name}: {e}")

        for flower_serial in flower_serials_to_water:
            self.env["flower.water"].create({
                "serial_id": flower_serial.id,
            })