# AWS CodeArtifact Python Proxy

Proxies requests to AWS CodeArtifact Python with HTTP Basic authentication and parametrized URL to download artifact directly ("generic package").
Use-case: source systems which cannot use any of the supported package managers and need a direct URL with HTTP Basic Authentication to download package.

Project consists of 2 parts:
- Containerized Flask application which accepts parametrized GET request, authenticates it and then makes an API call to a configured CodeArtifact repository to retrieve asset and then "proxy" it back to the requestor.
- Cloudformation templates which deploy ECS Cluster running this container with associated resources (ECR repository, ALB and associated subnets and Security Groups, SSM Parameter Store secrets). 
See attached Draw.IO diagram which describes what Cloudformation template deploy.
Sample pricing for AWS setup (PLEASE ADJUST NUMBERS BASED ON YOUR REQUIREMENTS) - https://calculator.aws/#/estimate?id=70a111e8b63b99a9f219aa7347d54d497ad5af15

## Preparation if you use CFN templates

- In the target AWS account, Create SSM Parameter Store SecureString for HTTP Auth Credentials. Parameter value format: username:password. Current CFN implementation supports only AWS-managed KMS key
- VPC for ECS and ALB Should be available in the target account - CFN creates subnets in 10.0.0.0/8 - adapt or parametrize networking config accordingly.
- VPC where container/task is deployed, should have internet access to access CodeArtifact

## Usage

1. Create a Docker container.
2. If not using ECS to run container but using  the docker-compose provided here, prepare the following env vars (create .env file in the root of the project)

| Env Var                   | Value                                                                                     |
| ------------------------- | ----------------------------------------------------------------------------------------- |
| `CODE_ARTIFACT_REGION`     | AWS Region<br>e.g. `ap-southeast-2`                                                       |
| `CODE_ARTIFACT_ACCOUNT_ID` | AWS Account ID<br>e.g. `123456789012`                                                     |
| `CODE_ARTIFACT_DOMAIN`     | AWS CodeArtifact domain name<br>e.g. `mycompany`                                          |
| `CODE_ARTIFACT_REPOSITORY` | AWS CodeArtifact repository name<br>e.g. `pypi-store`                                     |
| `PROXY_AUTH`              | Optional<br>HTTP Basic auth credentials expected by the proxy<br>e.g. `username:password` |

Cloudformation template uses SSM Parameter Store to securely store values which it is then passing to ECS task as environment variables.

3. The container exposes on port 5000, you can then use this container to pull packages from CodeArtifact.

4a. [Not using ECS] To run using docker-compose, do:

```
$ docker-compose up --build
```
Once application runs, make GET request to the service as described below

4b. If using Cloudformation template, procedure is the following:
- Run ecr-repo.yml to create ECR repository for container
- Build and then push container to ECR;
- Create SSM Parameter Store SecureString for HTTP Auth Credentials (see above)
- Deploy ecs-task-cfn.yml file which will deploy ECS cluster, task, ALB and associated subnets, Security Groups and IAM roles.

5. Once Flask application is running, construct URL to retrieve asset from CodeArtifact, for example:
wget --user=<username> --password=<password> 'http://<container IP and port or AWS ALB DNS Name>?namespace=my-ns&package=my-package&version=1.0.0&asset=unicorn.png'

