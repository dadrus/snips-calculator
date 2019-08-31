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
INTENT_NAME = "dadrus:Div"

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

def subscribe_intent_callback(hermes, intent_message):
    conf = read_configuration_file(CONFIG_INI)
    action_wrapper(hermes, intent_message, conf)


def action_wrapper(hermes, intent_message, conf): 
    print ("Intent Message {}".format(intent_message.__dict__))
    print ('Intent Message confidence score: {}'.format(intent_message.intent.confidence_score))
    print ('Intent Message intent name: {}'.format(intent_message.intent.intent_name))
    print ('Intent Message site id: {}'.format(intent_message.site_id))
    print ('Intent Message session id: {}'.format(intent_message.session_id))
    print ('Intent Message input: {}'.format(intent_message.input))
    print ('Intent Message slots: {}'.format(intent_message.slots.__dict__))
    if intent_message.slots and intent_message.slots['NumberOne']:
        print ('Intent Message slots 0: {}'.format(intent_message.slots.NumberOne.__dict__))
        print ('Intent Message slots 0: {}'.format(intent_message.slots.NumberOne.first().__dict__))
        print ('Intent Message slots 0: {}'.format(intent_message.slots.NumberOne.all()))
        for slot in intent_message.slots.NumberOne:
            name = slot.slot_name
            confidence = slot.confidence_score
            print("For slot : {}, the confidence is : {}".format(name, confidence))
            print("Slot {}: ".format(slot))
        print("For slot : {}, the confidence is : {}".format(intent_message.slots.NumberOne[0].slot_name, intent_message.slots.NumberOne[0].confidence_score))

    if intent_message.slots and intent_message.slots['NumberTwo']:
        print ('Intent Message slots 1: {}'.format(intent_message.slots.NumberTwo.__dict__))
        print ('Intent Message slots 1: {}'.format(intent_message.slots.NumberTwo.first().__dict__))
    
    print ('Intent Message custom data: {}'.format(intent_message.custom_data))

    current_session_id = intent_message.session_id
    
    if len(intent_message.slots) != 2:
        hermes.publish_continue_session(current_session_id, "Ich habe dich nicht verstanden. Wiederhole bitte die Aufgabe", INTENT_NAME)
        return

    num_one = intent_message.slots.NumberOne
    num_two = intent_message.slots.NumberTwo

    if(num_one[0].confidence_score < 0.8):
        hermes.publish_continue_session(current_session_id, "Ich habe die erste Zahl nicht verstanden. Wiederhole bitte die Aufgabe", INTENT_NAME)
        return

    if(num_two[0].confidence_score < 0.8):
        hermes.publish_continue_session(current_session_id, "Ich habe die zweite Zahl nicht verstanden. Wiederhole bitte die Aufgabe", INTENT_NAME)
        return

    A = int(num_one.first().value)
    B = int(num_two.first().value)
    
    result_sentence = ""
    try:
        C = A / B
        result_sentence = "Die Antwort ist: {}".format(str(C))
    except ZeroDivisionError :
        result_sentence = "Division durch 0 ist nicht möglich"
    
    
    hermes.publish_end_session(current_session_id, result_sentence)
    


if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent(INTENT_NAME, subscribe_intent_callback) \
         .start()
