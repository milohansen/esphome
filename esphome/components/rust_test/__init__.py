import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import CONF_ID

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(cg.Component),
})

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    cg.mark_as_rust(var)
