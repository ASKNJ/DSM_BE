import json
import pytest
from pytest_mock import mocker
from moto import mock_dynamodb
from lambdas.index import handler
import boto3

# Fixture to mock DynamoDB
@pytest.fixture
def dynamodb_mock():
    with mock_dynamodb():
        yield

# Test cases for lambda handler and helper methods
def test_save_impact_data(mocker, dynamodb_mock):
    """
    1. Mock DynamoDB.Table.put_item
    2. Sample event data
    3. Call the Lambda function
    4. Assertions
    """
    mocker.patch("boto3.resource").return_value.Table("impact_detail").put_item


    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "detail": [
                {"impact_id": 1, "category_id": 1, "impact_value": 100, "impact_percent": 50}
            ],
            "contribution": [
                {"impact_id": 1, "contrib_value": 50}
            ]
        })
    }

    response = handler(event, None)

    assert response["statusCode"] == 201
    assert "message" in list(response["body"])[0]

def test_get_data_by_id(mocker, dynamodb_mock):
    """
    test path params function handler
    1. Mock DynamoDB.Table.query
    2. Sample event data
    3. Call the Lambda function
    4. Assertions
    """

    mocker.patch("boto3.resource").return_value.Table('impact_contribution').query.return_value = {
        "Items": [
           {
            "impact_id": 3,
            "contrib_id_type": "2#1#other",
            "contrib_value": 4
        },
        {
            "impact_id": 3,
            "contrib_id_type": "2#category",
            "contrib_value": 13
        }
        ]
    }

    event = {
        "httpMethod": "GET",
        "pathParameters": {"fpid": '1'}
    }

    response = handler(event, None)

    assert response["statusCode"] == 200
    assert "contrib_id_type" in list(response["body"])[0]

def test_get_impacts_data(mocker, dynamodb_mock):
    """
    test query params function handler
    1. Mock DynamoDB.Table.query
    2. Sample event data
    3. Call the Lambda function
    4. Assertions
    """
    mocker.patch("boto3.resource").return_value.Table('impact_detail').query.return_value = {
        "Items": [
           {
            "category_id": 2,
            "impact_id": 3,
            "impact_name": "Climate change - land use and transform",
            "impact_type": "land",
            "impact_value": 345,
            "impact_percent": 21
        }
        ]
    }

    event = {
        "httpMethod": "GET",
        "queryStringParameters": {"cat": "2"}
    }
    response = handler(event, None)
    assert response["statusCode"] == 200
    assert "category_id" in list(response["body"])[0]
