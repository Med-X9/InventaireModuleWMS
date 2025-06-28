pipeline {
    agent any

    environment {
        FRONTEND_REPO = 'https://github.com/Med-X9/inventaireModuleWMSFront.git'
        BACKEND_REPO  = 'https://github.com/Med-X9/InventaireModuleWMS.git'

        IMAGE_PREFIX = 'oussamafannouch'
        FRONTEND_IMAGE = "${IMAGE_PREFIX}/frontend-app"
        BACKEND_IMAGE  = "${IMAGE_PREFIX}/backend-app"
        IMAGE_TAG = "latest"

        DEPLOY_HOST = '147.93.55.221'
        DEPLOY_USER = credentials('dev-test-creds') 
    }

    stages {
        stage('Clone Repositories') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'git-cred', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                    sh '''
                        rm -rf /tmp/frontend /tmp/backend
                        git clone --single-branch --branch devops https://$GIT_USER:$GIT_PASS@github.com/Med-X9/InventaireModuleWMS.git /tmp/backend
                    '''
                }
            }
        }

        stage('Build Backend Docker Image') {
            steps {
                dir('/tmp/backend') {
                    sh 'docker build -t $BACKEND_IMAGE:$IMAGE_TAG .'
                }
            }
        }

        stage('Push Docker Images') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', passwordVariable: 'PASS', usernameVariable: 'USER')]) {
                        sh "echo $PASS | docker login -u $USER --password-stdin"
                    }
                    sh 'docker push $BACKEND_IMAGE:$IMAGE_TAG'
                }
            }
        }

        stage('Uploading Files') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p /tmp/deployment/backend"
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p /tmp/deployment/frontend"

                        # Backend uploads
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/docker-compose.yml "$USER@$DEPLOY_HOST:/tmp/deployment/backend/docker-compose.yml"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/Dockerfile "$USER@$DEPLOY_HOST:/tmp/deployment/backend/Dockerfile"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/.env.prod "$USER@$DEPLOY_HOST:/tmp/deployment/backend/.env.prod"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/requirements.txt "$USER@$DEPLOY_HOST:/tmp/deployment/backend/requirements.txt"
                        sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no /tmp/backend/nginx "$USER@$DEPLOY_HOST:/tmp/deployment/backend/nginx"

                    '''
                }
            }
        }

        stage('Deploy Backend on Remote Server') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh root@147.93.55.221 "bash -c 'cd /tmp/deployment/backend && docker-compose pull && docker-compose up -d'"
                    '''
                }
            }
        }
    }
}
