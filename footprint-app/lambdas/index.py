import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json
import os
import logging
from datetime import datetime
from decimal import Decimal
import traceback
logger = logging.getLogger(__name__)


def handler(event, context):
    """
    Main handler that distributes POST, GET and GET with path params.
    Validations on handling all categories where it will be -1 for ALL_CATEGORIES.
    and rest will be mapped as per category id.
    event: get the event meta parameters.
    context: if any conetxt is passed, none passed 
    """
    try:
        method = event.get("httpMethod")
        impact_id = event.get("pathParameters", None)
        q_params = event.get("queryStringParameters", {})
        ddb = boto3.resource("dynamodb")
        if method.upper() == 'POST':
            data = json.loads(event.get('body', {}))
            response = save_impact_data(data, ddb)
        elif method.upper() == 'GET' and impact_id is not None:
            response = get_data_by_id(impact_id['fpid'], ddb)
        else:
            if q_params is None:
                response = get_impacts_data(-1, ddb)
            else:
                category_id = q_params.get("cat", None)
                if category_id is not None and category_id != '':
                    response = get_impacts_data(category_id, ddb)
                else:
                    raise ValueError("Invalid category")
        return {"statusCode": response['status'],
            "headers": {
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Content-Type': 'application/json',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        },
        "body": {json.dumps(response.get('data', {}))}
        }
    except Exception as err:
        traceback.print_exc()
        return {"statusCode": 403,
            "headers": {
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Headers':'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Content-Type': 'application/json',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        },
        "body": json.dumps({"error": str(err)})
        }
    
def get_data_by_id(impact_id, ddb):
    """
    Helper method to get the impact by id with all category type and other type data.
    ddb is the dynamo db instance which is initialized in main handler to pass the dynamo db botocore instance.
    """
    try:
        tbl_impact_contrib = os.environ['TBL_IMPACT_CONTRIBUTION']
        tic = ddb.Table(tbl_impact_contrib)
        items = tic.query(KeyConditionExpression=Key('impact_id').eq(int(impact_id)))
        data = items.get('Items', [])
        for item in data:
            for key,value in item.items():
                if isinstance(value, Decimal) and value % 1 == 0:
                    item[key] = int(value)
        return {'status': 200, 'data': data}
    except ClientError as err:
        traceback.print_exc()
        logger.exception("Couldn't load data into table due to %s.",err)
        return {'status': 400, 'data': {'error': err.args}}

def save_impact_data(data, ddb):
    """
    Helper method to save the data by post request.
    data: it is the payload for detail and contributions
    if any of it is not passed as key then no data will be added.
    ddb: dynamodb botocore instance.
    """
    try:
        tbl_impact_detail = os.environ.['TBL_IMPACT_DETAIL']
        tbl_impact_contrib = os.environ.get['TBL_IMPACT_CONTRIBUTION']
        tid, tic = ddb.Table(tbl_impact_detail), ddb.Table(tbl_impact_contrib)
        details = data.get('detail', None)
        contributions = data.get('contribution', None)
        now = int(datetime.now().timestamp())
        
        if details is not None or contributions is not None:
            for detail in details:
                detail['impact_id'] = int(detail['impact_id'])
                detail['category_id'] = int(detail['category_id'])
                detail['impact_value'] = int(detail['impact_value'])
                detail['impact_percent'] = int(detail['impact_percent'])
                if detail['impact_percent'] > 100:
                    raise ValueError("Invalid attribute value: impact_percent")
                detail['created_at'] = now
                tid.put_item(Item=detail)
            for contribution in contributions:
                contribution['impact_id'] = int(contribution['impact_id'])
                contribution['contrib_value'] = int(contribution['contrib_value'])
                contribution['created_at'] = now
                tic.put_item(Item=contribution)
        else:
            return {'status': 400, 'data': {'error': 'Invalid payload'}}
        return {'status': 201, 'data': {'message': f"Impacts for categories created at {now}"}}
    except ClientError as err:
        logger.exception("Couldn't load data into table due to %s.",err)
        return {'status': 400, 'data': {'error': err.args}}
    except KeyError as err:
        return {'status': 400, 'data': {'error': str(err), 'message': 'invalid payload'}}
    except ValueError as err:
        return {'status': 400, 'data': {'error': str(err), 'message': 'invalid payload'}}
        

def get_impacts_data(category_id, ddb):
    """
    Helper method to get all impacts per category selected.
    category_id: to get the data per category id, -1 incaseof all categories needed.
    ddb: Dynamodb botocore instance.
    """
    try:
        tbl_impact_detail = os.environ['TBL_IMPACT_DETAIL']
        imp_det = ddb.Table(tbl_impact_detail)
        data = []
        if category_id == -1:
            categories = [1,2,3]
            for category in categories:
                items = imp_det.query(KeyConditionExpression=Key('category_id').eq(int(category)))    
                data = [*data, *items.get('Items', [])]
        else:
            items = imp_det.query(KeyConditionExpression=Key('category_id').eq(int(category_id)))
            data = items.get('Items', [])
        for item in data:
            for key,value in item.items():
                if isinstance(value, Decimal) and value % 1 == 0:
                    item[key] = int(value)
        return {'status': 200, 'data': data}
    except ClientError as err:
        traceback.print_exc()
        logger.exception("Couldn't load data into table due to %s.",err)
        return {'status': 400, 'data': {'error': err.args}}