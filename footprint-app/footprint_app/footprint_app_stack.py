from aws_cdk import (
    Duration,
    Stack,
    aws_cognito as cognito,
    aws_apigateway as apigateway
    # aws_sqs as sqs,
)
from constructs import Construct


class FootprintAppStack(Stack):
    """
    FootprintAppStack to deploy cognito user pool for authorization with settings:
    Implemented as client credentials with private key clientid and client private secret key used 
    for demonstration purpose running app on local.
    read and write scope with OAuth2.0 authentication for access token.
    """
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        user_pool = cognito.UserPool(
            self, "MyUserPool",
            user_pool_name="FpApiUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases={"username": True, "email": True},
        )
        resource_server = user_pool.add_resource_server(
            "MyResourceServer",
            identifier="fp-api-resource-server",
            scopes=[
                cognito.ResourceServerScope(
                    scope_name="read",
                    scope_description="Read access"
                ),
                cognito.ResourceServerScope(
                    scope_name="write",
                    scope_description="Write access"
                )
            ]
        )
        read_only_scope = cognito.ResourceServerScope(scope_name="read", scope_description="Read-only access")
        write_only_scope = cognito.ResourceServerScope(scope_name="write", scope_description="Write-only access")
        
        app_client = user_pool.add_client(
            "MyAppClient",
            user_pool_client_name='fp-api-app-client',
            auth_flows={
                "user_srp": True
            },
            generate_secret=True,
            access_token_validity=Duration.minutes(60),  # Set access token validity
            id_token_validity=Duration.minutes(60),  # Set ID token validity
            refresh_token_validity=Duration.days(30),  # Set refresh token validity
            enable_token_revocation=True,
            prevent_user_existence_errors=True,
            o_auth={
                "scopes": [
                    cognito.OAuthScope.resource_server(resource_server, read_only_scope),
                    cognito.OAuthScope.resource_server(resource_server, write_only_scope)
                ],
                "flows": cognito.OAuthFlows(
                    client_credentials=True
                )
            }
        )

        user_pool.add_domain(
            "MyCognitoDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="fp-api-v1",  # Specify your custom domain prefix
            )
        )
