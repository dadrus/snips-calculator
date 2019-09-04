
import json
from unittest.mock import Mock

from hermes_python.ontology.dialogue.intent import IntentClassifierResult
from hermes_python.ontology.dialogue.intent import IntentMessage
from hermes_python.ontology.dialogue.slot import NluSlot
from hermes_python.ontology.dialogue.slot import NumberValue
from hermes_python.ontology.dialogue.slot import SlotMap
from hermes_python.ontology.dialogue.slot import SlotValue
import pytest

import importlib.util as imlib


spec = imlib.spec_from_file_location('calc', 'action-dadrus-Div-dadrus.My_Calculator.py')
module = imlib.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def test_intent():
    return  IntentMessage(
        "foo", json.dumps({ "request_count": 0 }), "bla", "user input",
        IntentClassifierResult("intent name", 1.0),
        None)


@pytest.fixture  
def test_config():
    conf = { "global": {} }
    return conf


def test_dialogue_is_aborted_when_request_count_is_above_3(test_config, test_intent):
    # given
    hermes = Mock()
    test_intent.custom_data = json.dumps({ "request_count": 3 })

    # when
    module.action_wrapper(hermes, test_intent, test_config)

    # then
    hermes.publish_end_session.assert_called_once_with(test_intent.session_id, "Ich muss aufgeben. Ich kann dich überhaupt nicht verstehen")
    hermes.publish_continue_session.assert_not_called()


def test_dialogue_is_continued_if_the_amount_of_the_recognized_slots_is_zero(test_config, test_intent):
    # given
    hermes = Mock()

    # when
    module.action_wrapper(hermes, test_intent, test_config)

    # then
    hermes.publish_end_session.assert_not_called()
    hermes.publish_continue_session.assert_called_once_with(
        test_intent.session_id,
        "Ich habe dich nicht verstanden. Wiederhole bitte die Aufgabe",
        [module.INTENT_NAME], json.dumps({ "request_count": 1 }))

    
def test_dialogue_is_continued_if_the_amount_of_the_recognized_slots_is_one(test_config, test_intent):
    # given
    hermes = Mock()
    
    test_intent.slots = SlotMap({
         "NumberOne": [ NluSlot(0.8, SlotValue(int, NumberValue(2)), "2", "2 entity", "NumberOne", 0, 1) ]
         })

    # when
    module.action_wrapper(hermes, test_intent, test_config)

    # then
    hermes.publish_end_session.assert_not_called()
    hermes.publish_continue_session.assert_called_once_with(
        test_intent.session_id,
        "Ich habe dich nicht verstanden. Wiederhole bitte die Aufgabe",
        [module.INTENT_NAME], json.dumps({ "request_count": 1 }))


def test_first_number_is_requested_again_if_the_confidence_score_is_less_then_the_configured_threshold(test_config, test_intent):
    # given
    hermes = Mock()
    test_config["global"] = { "confidence_score_threshold": 0.9 }

    val1 = NumberValue(2)
    val1_confidence_score = 0.8
    val2 = NumberValue(3)
    val2_confidence_score = 1.0
    test_intent.slots = SlotMap({
         "NumberOne": [ NluSlot(val1_confidence_score, SlotValue(int, val1), "2", "2 entity", "NumberOne", 0, 1) ],
         "NumberTwo": [ NluSlot(val2_confidence_score, SlotValue(int, val2), "3", "3 entity", "NumberTwo", 0, 1) ] 
         })

    # when
    module.action_wrapper(hermes, test_intent, test_config)

    # then
    hermes.publish_end_session.assert_not_called()
    hermes.publish_continue_session.assert_called_once_with(
        test_intent.session_id,
        "Ich habe die erste Zahl nicht verstanden. Wiederhole bitte die erste Zahl",
        [module.INTENT_NAME],
        json.dumps({ "request_count": 1, "b": val2.value, "b_confidence_score": val2_confidence_score })
        )


def test_second_number_is_requested_again_if_the_confidence_score_is_less_then_the_configured_threshold(test_config, test_intent):
    # given
    hermes = Mock()
    test_config["global"] = { "confidence_score_threshold": 0.9 }
    
    val1 = NumberValue(2)
    val1_confidence_score = 1.0
    val2 = NumberValue(3)
    val2_confidence_score = 0.8
    test_intent.slots = SlotMap({
         "NumberOne": [ NluSlot(val1_confidence_score, SlotValue(int, val1), "2", "2 entity", "NumberOne", 0, 1) ],
         "NumberTwo": [ NluSlot(val2_confidence_score, SlotValue(int, val2), "3", "3 entity", "NumberTwo", 0, 1) ] 
         })
    
    # when
    module.action_wrapper(hermes, test_intent, test_config)

    # then
    hermes.publish_end_session.assert_not_called()
    hermes.publish_continue_session.assert_called_once_with(
        test_intent.session_id,
        "Ich habe die zweite Zahl nicht verstanden. Wiederhole bitte die zweite Zahl",
        [module.INTENT_NAME],
        json.dumps({ "request_count": 1, "a": val1.value, "a_confidence_score": val1_confidence_score })
        )

    
def test_successful_division(test_config, test_intent):
    # given
    hermes = Mock()
    
    test_intent.slots = SlotMap({
         "NumberOne": [ NluSlot(1.0, SlotValue(int, NumberValue(4)), "4", "4 entity", "NumberOne", 0, 1) ],
         "NumberTwo": [ NluSlot(1.0, SlotValue(int, NumberValue(2)), "2", "2 entity", "NumberTwo", 0, 1) ] 
         })
    
    # when
    module.action_wrapper(hermes, test_intent, test_config)

    # then
    hermes.publish_end_session.assert_called_once_with(test_intent.session_id, "Die Antwort ist: 2.0")
    hermes.publish_continue_session.assert_not_called()

    
def test_division_by_zero(test_config, test_intent):
    # given
    hermes = Mock()
    
    test_intent.slots = SlotMap({
         "NumberOne": [ NluSlot(1.0, SlotValue(int, NumberValue(4)), "4", "4 entity", "NumberOne", 0, 1) ],
         "NumberTwo": [ NluSlot(1.0, SlotValue(int, NumberValue(0)), "0", "0 entity", "NumberTwo", 0, 1) ] 
         })
    
    # when
    module.action_wrapper(hermes, test_intent, test_config)

    # then
    hermes.publish_end_session.assert_called_once_with(test_intent.session_id, "Division durch 0 ist nicht möglich")
    hermes.publish_continue_session.assert_not_called()
