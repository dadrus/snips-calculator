#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from hermes_python.hermes import Hermes
from hermes_python.ffi.utils import MqttOptions
from hermes_python.ontology import *
import io
import logging

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

_LOGGER = logging.getLogger(__name__)

class SnipsConfigParser(configparser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        return dict()

def subscribe_intent_callback(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    action_wrapper(hermes, intentMessage, conf)


def action_wrapper(hermes, intentMessage, conf):
    _LOGGER.debug("Simple debug message")
    _LOGGER.info("Simple info message")
    _LOGGER.error("Simple error message")
    _LOGGER.warn("Simple warn message")
    _LOGGER.debug(intentMessage)

    print ('[Received] intent: {}'.format(intentMessage.intent.intent_name))

    A = int(intentMessage.slots.NumberOne.first().value)
    B = int(intentMessage.slots.NumberTwo.first().value)
    
    result_sentence = ""
    try:
        C = A / B
        result_sentence = "Die Antwort ist: {}".format(str(C))
    except ZeroDivisionError :
        result_sentence = "Division durch 0 ist nicht möglich"
    
    
    current_session_id = intentMessage.session_id
    hermes.publish_end_session(current_session_id, result_sentence)
    


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent("dadrus:Div", subscribe_intent_callback) \
         .start()
