from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    RemovalPolicy,
    aws_cognito as cognito
)
from aws_cdk.aws_apigateway import (
    LambdaIntegration,
    RestApi,
    AuthorizationType,
    CognitoUserPoolsAuthorizer,
    CorsOptions,
    Cors,
    Stage,
    Deployment
)
from aws_cdk.aws_lambda import Function, Runtime, Code
from constructs import Construct
from datetime import datetime


class FootprintApiDbStack(Stack):
    """
    Stack for building lambda, API gateway and dynamo db tables.
    Service role is managed on dynamodb with lambda access role to connect to dynamodb with readand write roles.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # My Lambda handler for API that acts as both consumer and producer for db
        consumer_producer_lambda = Function(
            self,
            "MyLambdaFunction",
            function_name="footprintApiCollect",
            description=f'Generated on {int(datetime.now().timestamp())}',
            runtime=Runtime.PYTHON_3_9,
            handler="index.handler",
            code=Code.from_asset("lambdas"),  # relative folder path to directory
            environment={
                'TBL_IMPACT_DETAIL': 'impact_detail',
                'TBL_IMPACT_CONTRIBUTION': 'impact_contribution'
            }
        )


        user_pool = cognito.UserPool.from_user_pool_id(self, 'ExistingUserPool', 'ap-south-1_xoBx2f6RG')

         # Create REST API Gateway
        rest_api = RestApi(
            self, "RestApi", rest_api_name="footprint-api", description="footprint api",
            default_cors_preflight_options=CorsOptions(
                allow_origins=Cors.ALL_ORIGINS,
                allow_headers=['Content-Type','X-Amz-Date','Authorization','X-Api-Key','X-Amz-Security-Token'],
                allow_methods=['GET', 'POST', 'OPTIONS']
            )
        )

        # Add Resource 'fp-api'
        fp_api_resource = rest_api.root.add_resource("footprints")

        # Create Authorizer from cognito in API gateway
        auth = CognitoUserPoolsAuthorizer(self, "fpApiAuthorizer", cognito_user_pools=[user_pool])

        # Add GET Method to 'footprint/' endpoint
        get_integration = LambdaIntegration(consumer_producer_lambda)

        fp_api_resource.add_method(
            "GET",
            get_integration,
            authorization_type=AuthorizationType.COGNITO,
            authorizer=auth,
            authorization_scopes=['fp-api-resource-server/read']
        )

        # Add POST Method to 'footprint/' endpoint
        post_integration = LambdaIntegration(consumer_producer_lambda)

        fp_api_resource.add_method(
            "POST",
            post_integration,
            authorization_type=AuthorizationType.COGNITO,
            authorizer=auth,
            authorization_scopes=['fp-api-resource-server/write']
        )

        # Add GET method to get impacts by fottprint ids /footprints/{fpid}
        fp_api_by_id = fp_api_resource.add_resource("{fpid}")

        fp_api_by_id.add_method("GET", 
            get_integration,
            authorization_type=AuthorizationType.COGNITO,
            authorizer=auth,
            authorization_scopes=['fp-api-resource-server/read']
            )

        deployment = Deployment(self, "Deployment", api=rest_api)

        
        # create table impact_details to get all impacts per category change in dropdown.
        tbl_impact_detail = dynamodb.Table(self, "impact_detail",
            table_name='impact_detail',
            partition_key=dynamodb.Attribute(
                name="category_id",
                type=dynamodb.AttributeType.NUMBER
            ),
            sort_key=dynamodb.Attribute(name='impact_id', type=dynamodb.AttributeType.NUMBER),
            removal_policy=RemovalPolicy.DESTROY
        )

        # We also have to show all category contributions per impact with impact_id as a input.
        tbl_impact_contibution = dynamodb.Table(self, "impact_contribution",
            table_name='impact_contribution',
            partition_key=dynamodb.Attribute(
                name="impact_id",
                type=dynamodb.AttributeType.NUMBER
            ),
            sort_key=dynamodb.Attribute(name='contrib_id_type', type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY
        )
        tbl_impact_detail.grant_read_write_data(consumer_producer_lambda)
        tbl_impact_contibution.grant_read_write_data(consumer_producer_lambda)