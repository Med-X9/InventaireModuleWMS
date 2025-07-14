pipeline {
    agent any

    environment {
        BACKEND_REPO  = 'https://github.com/Med-X9/InventaireModuleWMS.git'
        IMAGE_PREFIX = 'oussamafannouch'
        BACKEND_IMAGE  = "${IMAGE_PREFIX}/backend-app"
        IMAGE_TAG = "latest"
        
        DEPLOY_HOST  = "${env.BRANCH_NAME == 'main' ? '31.97.158.68' : (env.BRANCH_NAME == 'dev' ? '147.93.55.221' : '')}"
        DEPLOY_CREDS = "${env.BRANCH_NAME == 'main' ? 'prod-creds' : (env.BRANCH_NAME == 'dev' ? 'dev-test-creds' : '')}"
        ENV_NAME     = "${env.BRANCH_NAME == 'main' ? 'production' : (env.BRANCH_NAME == 'dev' ? 'development' : '')}"
    }

    stages {
        stage('Check Branch') {
            steps {
                script {
                    if (env.BRANCH_NAME != 'dev' && env.BRANCH_NAME != 'main') {
                        echo "Skipping deployment - not on dev or main branch. Current branch: ${env.BRANCH_NAME}"
                        currentBuild.result = 'SUCCESS'
                        return
                    }
                    echo "Proceeding with deployment on ${env.BRANCH_NAME} branch to ${env.ENV_NAME} environment"
                    echo "Deploy target: ${env.DEPLOY_HOST}"
                }
            }
        }

        stage('Clone Repositories') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'git-cred', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                    sh '''
                        rm -rf /tmp/backend
                        git clone --single-branch --branch ${BRANCH_NAME} https://$GIT_USER:$GIT_PASS@github.com/Med-X9/InventaireModuleWMS.git /tmp/backend
                    '''
                }
            }
        }

        stage('Build Backend Docker Image') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                dir('/tmp/backend') {
                    script {
                        def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                        sh "docker build -t ${BACKEND_IMAGE}:${imageTag} ."
                        sh "docker tag ${BACKEND_IMAGE}:${imageTag} ${BACKEND_IMAGE}:${IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Push Docker Images') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', passwordVariable: 'PASS', usernameVariable: 'USER')]) {
                        sh "echo $PASS | docker login -u $USER --password-stdin"
                    }
                    def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                    sh "docker push ${BACKEND_IMAGE}:${imageTag}"
                    sh "docker push ${BACKEND_IMAGE}:${IMAGE_TAG}"
                }
            }
        }

        stage('Uploading Files') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: env.DEPLOY_CREDS, usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        sh '''
                            sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "rm -rf /tmp/deployment/backend && mkdir -p /tmp/deployment/backend"
                            sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no /tmp/backend/. "$USER@$DEPLOY_HOST:/tmp/deployment/backend/"
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no "/tmp/backend/.env copy" "$USER@$DEPLOY_HOST:/tmp/deployment/backend/.env"
                        '''
                    }
                }
            }
        }

        stage('Deploy Backend on Remote Server') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: env.DEPLOY_CREDS, usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        sh '''
                            ssh "$USER@$DEPLOY_HOST" "bash -c 'cd /tmp/deployment/backend && docker-compose down && docker-compose pull && docker-compose up -d'"
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                if (env.BRANCH_NAME == 'dev') {
                    echo "✅ Deployment to development environment (${env.DEPLOY_HOST}) completed successfully!"
                } else if (env.BRANCH_NAME == 'main') {
                    echo "✅ Deployment to production environment (${env.DEPLOY_HOST}) completed successfully!"
                } else {
                    echo "✅ Pipeline completed - no deployment needed for branch: ${env.BRANCH_NAME}"
                }
            }
        }
        failure {
            script {
                if (env.BRANCH_NAME == 'dev' || env.BRANCH_NAME == 'main') {
                    echo "❌ Pipeline failed for ${env.ENV_NAME} deployment!"
                } else {
                    echo "❌ Pipeline failed!"
                }
            }
        }
    }
}
