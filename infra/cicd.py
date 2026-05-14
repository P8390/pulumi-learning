import pulumi
import pulumi_aws as aws

config = pulumi.Config()

github_token = config.require_secret("githubToken")
github_owner = "P8390"
repo_name = "pulumi-learning"
branch = "main"


build_role = aws.iam.Role(
    "build-role",
    assume_role_policy="""{
      "Version":"2012-10-17",
      "Statement":[{
        "Action":"sts:AssumeRole",
        "Principal":{
          "Service":"codebuild.amazonaws.com"
        },
        "Effect":"Allow"
      }]
    }"""
)

aws.iam.RolePolicyAttachment(
    "build-admin",
    role=build_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "AdministratorAccess"
    )
)

project = aws.codebuild.Project(
    "pulumi-build",

    service_role=build_role.arn,

    artifacts={
        "type": "CODEPIPELINE"
    },

    environment={
        "compute_type":
            "BUILD_GENERAL1_SMALL",

        "image":
            "aws/codebuild/standard:7.0",

        "type":
            "LINUX_CONTAINER"
    },

    source={
        "type":"CODEPIPELINE",
        "buildspec":"buildspec.yml"
    }
)

pipeline_role = aws.iam.Role(
    "pipeline-role",
    assume_role_policy="""{
      "Version":"2012-10-17",
      "Statement":[{
        "Action":"sts:AssumeRole",
        "Principal":{
          "Service":"codepipeline.amazonaws.com"
        },
        "Effect":"Allow"
      }]
    }"""
)

aws.iam.RolePolicyAttachment(
    "pipeline-admin",
    role=pipeline_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "AdministratorAccess"
    )
)

artifact_bucket = aws.s3.Bucket(
    "pipeline-artifacts"
)

pipeline = aws.codepipeline.Pipeline(
    "platform-pipeline",

    role_arn=pipeline_role.arn,

    artifact_stores=[{
        "location": artifact_bucket.bucket,
        "type": "S3"
    }],
    stages=[

        {
            "name":"Source",
            "actions":[{
                "name":"GitHub",
                "category":"Source",
                "owner":"ThirdParty",
                "provider":"GitHub",
                "version":"1",

                "outputArtifacts":["source"],

                "configuration":{
                    "Owner": github_owner,
                    "Repo": repo_name,
                    "Branch": branch,
                    "OAuthToken":
                        github_token
                }
            }]
        },

        {
            "name":"Deploy",
            "actions":[{
                "name":"Deploy",

                "category":"Build",
                "owner":"AWS",
                "provider":"CodeBuild",
                "version":"1",

                "inputArtifacts":
                    ["source"],

                "configuration":{
                    "ProjectName":
                        project.name
                }
            }]
        }
    ]
)
