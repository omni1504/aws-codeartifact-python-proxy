# AWS CodeArtifact Python Proxy

Proxies requests to AWS CodeArtifact Python with HTTP Basic authentication and parametrized URL to download artifact directly 



## Preparation if you use CFN templates

- In the target AWS account, Create SSM Parameter Store SecureString for HTTP Auth Credentials. Parameter value format: username:password. Current CFN implementation supports only AWS-managed KMS key
- VPC for ECS and ALB Should be available in the target account - CFN creates subnets in 10.0.0.0/8 - adapt or parametrize networking config accordingly.
- VPC where container/task is deployed, should have internet access to access CodeArtifact

## Usage

1. Create a Docker container container, prepare  the following env vars

| Env Var                   | Value                                                                                     |
| ------------------------- | ----------------------------------------------------------------------------------------- |
| `CODE_ARTIFACT_REGION`     | AWS Region<br>e.g. `ap-southeast-2`                                                       |
| `CODE_ARTIFACT_ACCOUNT_ID` | AWS Account ID<br>e.g. `123456789012`                                                     |
| `CODE_ARTIFACT_DOMAIN`     | AWS CodeArtifact domain name<br>e.g. `mycompany`                                          |
| `CODE_ARTIFACT_REPOSITORY` | AWS CodeArtifact repository name<br>e.g. `pypi-store`                                     |
| `PROXY_AUTH`              | Optional<br>HTTP Basic auth credentials expected by the proxy<br>e.g. `username:password` |

2. You may also pass in AWS credential environment variables or make credentials available some other way. If using the docker-compose provided here, you can use the `.env` template to do this.
CFN template uses SSM Parameter Store values which it is then passing to ECS task as environment variables.

The container exposes on port 5000, you can then use this container to pull packages from CodeArtifact.

To run using docker-compose, do:

```
$ docker-compose up --build
```

3. If using CFN template, procedure is the following:
- Run ecr-repo.yml to create ECR repository for container
- Build and then push container to ECR;
- Create SSM Parameter Store SecureString for HTTP Auth Credentials (see above)
- Deploy ecs-task-cfn.yml file which will deploy ECS cluster, task, ALB and associated subnets, Security Groups and IAM roles.

4. Sample pricing (PLEASE ADJUST NUMBERS BASED ON YOUR REQUIREMENTS) - https://calculator.aws/#/estimate?id=70a111e8b63b99a9f219aa7347d54d497ad5af15
