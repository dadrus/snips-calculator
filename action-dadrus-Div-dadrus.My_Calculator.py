#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import collections
import configparser
import io
import json

from hermes_python.ffi.utils import MqttOptions
from hermes_python.hermes import Hermes
from hermes_python.ontology import *


CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"
INTENT_NAME = "dadrus:Div"

try:
  # Python 2.7+
  basestring
except NameError:
  # Python 3.3+
  basestring = str 

def todict(obj):
  """ 
  Recursively convert a Python object graph to sequences (lists)
  and mappings (dicts) of primitives (bool, int, float, string, ...)
  """
  if isinstance(obj, basestring):
    return obj 
  elif isinstance(obj, dict):
    return dict((key, todict(val)) for key, val in obj.items())
  elif isinstance(obj, collections.Iterable):
    return [todict(val) for val in obj]
  elif hasattr(obj, '__dict__'):
    return todict(vars(obj))
  elif hasattr(obj, '__slots__'):
    return todict(dict((name, getattr(obj, name)) for name in getattr(obj, '__slots__')))
  return obj



def list_object_to_dict(lst):
    return_list = []
    for l in lst:
        return_list.append(object_to_dict(l))
    return return_list

def object_to_dict(object):
    dict = vars(object)
    for k,v in dict.items():
        if type(v).__name__ not in ['list', 'dict', 'str', 'int', 'float']:
                dict[k] = object_to_dict(v)
        if type(v) is list:
            dict[k] = list_object_to_dict(v)
    return dict



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
    print("action_wrapper")
    request_count_threshold = conf.get("global").get("request_count_threshold", 3)
    confidence_score_threshold = conf.get("global").get("confidence_score_threshold", 0.8)
    
    print(todict( intent_message))
    
    interaction_data = json.loads(intent_message.custom_data) if intent_message.custom_data else {}
    request_count = interaction_data.get("request_count", 0)
    request_count += 1
    interaction_data["request_count"] = request_count
    
    a = interaction_data.get("a", 0)
    b = interaction_data.get("b", 0)
    a_confidence_score = interaction_data.get("a_confidence_score", 0.0)
    b_confidence_score = interaction_data.get("b_confidence_score", 0.0)

    if request_count > request_count_threshold:
        hermes.publish_end_session(intent_message.session_id, "Ich muss aufgeben. Ich kann dich überhaupt nicht verstehen")
        return
    
    if len(intent_message.slots) != 2 and len(interaction_data) == 1:
        hermes.publish_continue_session(intent_message.session_id,
            "Ich habe dich nicht verstanden. Wiederhole bitte die Aufgabe",
            [INTENT_NAME],
            json.dumps(interaction_data))
        return

    a = a or int(intent_message.slots.NumberOne.first().value)
    b = b or int(intent_message.slots.NumberTwo.first().value)

    a_confidence_score = a_confidence_score or intent_message.slots.NumberOne[0].confidence_score
    b_confidence_score = b_confidence_score or intent_message.slots.NumberTwo[0].confidence_score

    if(a_confidence_score < confidence_score_threshold):
        interaction_data["b"] = b
        interaction_data["b_confidence_score"] = b_confidence_score
        hermes.publish_continue_session(intent_message.session_id, 
            "Ich habe die erste Zahl nicht verstanden. Wiederhole bitte die erste Zahl",
            [INTENT_NAME],
            json.dumps(interaction_data),
            slot_to_fill = "NumberOne")
        return

    if(b_confidence_score < confidence_score_threshold):
        interaction_data["a"] = a
        interaction_data["a_confidence_score"] = a_confidence_score
        hermes.publish_continue_session(intent_message.session_id,
            "Ich habe die zweite Zahl nicht verstanden. Wiederhole bitte die zweite Zahl",
            [INTENT_NAME],
            json.dumps(interaction_data),
            slot_to_fill = "NumberTwo")
        return
    
    result_sentence = ""
    try:
        result = a / b
        result_sentence = "Die Antwort ist: {}".format(str(result))
    except ZeroDivisionError :
        result_sentence = "Division durch 0 ist nicht möglich"
    
    hermes.publish_end_session(intent_message.session_id, result_sentence)
    
def session_started(hermes, started_message):
    print("session_started")
    print(todict(started_message))

def session_queued(hermes, queued_message):
    print("session_queued")
    print(todict(queued_message))

def session_ended(hermes, ended_message):
    print("session_ended")
    print(todict(ended_message))

if __name__ == "__main__":
    mqtt_opts = MqttOptions()
    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent(INTENT_NAME, subscribe_intent_callback) \
         .subscribe_session_started(session_started) \
         .subscribe_session_queued(session_queued) \
         .subscribe_session_ended(session_ended) \
         .start()
