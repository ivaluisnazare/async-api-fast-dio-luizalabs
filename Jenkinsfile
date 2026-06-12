pipeline {
    agent any

    environment {
        DOCKER_REGISTRY_CREDS = 'dockerhub-credentials-id'
        KUBECONFIG_CREDS      = 'kubeconfig-credentials-id'
        SONAR_SERVER_NAME     = 'SonarQube-Server'

        ACCOUNT_IMAGE         = "ivanazare/account-service:${BUILD_NUMBER}"
        USER_IMAGE            = "ivanazare/user-service:${BUILD_NUMBER}"
    }

    stages {
        stage('Initial Analysis & Setup') {
            steps {
                echo 'Starting the pipeline for the FastAPI stack...'
            }
        }

        stage('Testes & Quality (parallel)') {
            parallel {
                stage('CI - Account Service') {
                    steps {
                        dir('account') {
                            echo 'Running tests with Pytest for Account Service...'
                            sh '''
                                python3 -m venv .venv
                                . .venv/bin/activate
                                pip install -r requirements.txt pytest pytest-cov
                                pytest --cov=src --cov-report=xml:coverage.xml tests/
                            '''

                            withSonarQubeEnv("${env.SONAR_SERVER_NAME}") {
                                sh """
                                    sonar-scanner \
                                    -Dsonar.organization=ivaluisnazare \
                                    -Dsonar.projectKey=ivaluisnazare_async-api-fast-dio-luizalabs \
                                    -Dsonar.projectName=async-api-fast-dio-luizalabs \
                                    -Dsonar.sources=src \
                                    -Dsonar.tests=tests \
                                    -Dsonar.python.coverage.reportPaths=coverage.xml
                                """
                            }
                        }
                    }
                }

                stage('CI - User Service') {
                    steps {
                        dir('user') {
                            echo 'Running tests with Pytest for User Service...'
                            sh '''
                                python3 -m venv .venv
                                . .venv/bin/activate
                                pip install -r requirements.txt pytest pytest-cov
                                pytest --cov=src --cov-report=xml:coverage.xml tests/
                            '''

                            withSonarQubeEnv("${env.SONAR_SERVER_NAME}") {
                                sh """
                                    sonar-scanner \
                                    -Dsonar.organization=ivaluisnazare \
                                    -Dsonar.projectKey=ivaluisnazare_async-api-fast-dio-luizalabs \
                                    -Dsonar.projectName=async-api-fast-dio-luizalabs \
                                    -Dsonar.sources=src \
                                    -Dsonar.tests=tests \
                                    -Dsonar.python.coverage.reportPaths=coverage.xml
                                """
                            }
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    echo 'Awaiting response from SonarQube Quality Gate...'
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build & Push Images') {
            parallel {
                stage('Build Account') {
                    steps {
                        withCredentials([usernamePassword(credentialsId: "${env.DOCKER_REGISTRY_CREDS}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                            sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                            dir('account') {
                                sh "docker build -t ${env.ACCOUNT_IMAGE} -t ivanazare/account-service:latest ."
                                sh "docker push ${env.ACCOUNT_IMAGE}"
                                sh "docker push ivanazare/account-service:latest"
                            }
                        }
                    }
                }
                stage('Build User') {
                    steps {
                        withCredentials([usernamePassword(credentialsId: "${env.DOCKER_REGISTRY_CREDS}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                            sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                            dir('user') {
                                sh "docker build -t ${env.USER_IMAGE} -t ivanazare/user-service:latest ."
                                sh "docker push ${env.USER_IMAGE}"
                                sh "docker push ivanazare/user-service:latest"
                            }
                        }
                    }
                }
            }
        }

        stage('Deploy no Kubernetes') {
            steps {
                withCredentials([file(credentialsId: "${env.KUBECONFIG_CREDS}", variable: 'KUBECONFIG')]) {
                    echo 'Updating Deployments in the Kubernetes Cluster...'

                    sh "kubectl --kubeconfig=\$KUBECONFIG apply -f k8s/account-deployment.yaml"
                    sh "kubectl --kubeconfig=\$KUBECONFIG apply -f k8s/users-deployment.yaml"

                    sh "kubectl --kubeconfig=\$KUBECONFIG set image deployment/account-service account-service=${env.ACCOUNT_IMAGE} -n banking-operations"
                    sh "kubectl --kubeconfig=\$KUBECONFIG set image deployment/users-service users-service=${env.USER_IMAGE} -n banking-operations"

                    sh "kubectl --kubeconfig=\$KUBECONFIG rollout status deployment/account-service -n banking-operations"
                    sh "kubectl --kubeconfig=\$KUBECONFIG rollout status deployment/users-service -n banking-operations"
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline executed successfully and microservices updated!'
        }
        failure {
            echo 'The pipeline failed. Please check the logs above.'
        }
    }
}