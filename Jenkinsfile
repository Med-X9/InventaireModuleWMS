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
        DOCKER_COMPOSE_DIR = '/opt/deployment'
    }

        stage('Clone Repositories') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-creds', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                    sh '''
                        rm -rf frontend backend
                        git clone https://$GIT_USER:$GIT_PASS@github.com/Med-X9/inventaireModuleWMSFront.git frontend
                        git clone https://$GIT_USER:$GIT_PASS@github.com/Med-X9/InventaireModuleWMS.git backend
                    '''
                }
            }
        }


        stage('Build Frontend Docker Image') {
            steps {
                dir('frontend') {
                    sh 'docker build -t $FRONTEND_IMAGE:$IMAGE_TAG .'
                }
            }
        }

        stage('Build Backend Docker Image') {
            steps {
                dir('backend') {
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
                    sh 'docker push $FRONTEND_IMAGE:$IMAGE_TAG'
                    sh 'docker push $BACKEND_IMAGE:$IMAGE_TAG'
                }
            }
        }

        stage('Uploading Files') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p $DOCKER_COMPOSE_DIR/backend"
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p $DOCKER_COMPOSE_DIR/frontend"

                        # Backend uploads
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no backend/docker-compose.yml "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/backend/docker-compose.yml"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no backend/Dockerfile "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/backend/Dockerfile"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no backend/.env "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/backend/.env"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no backend/requirements.txt "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/backend/requirements.txt"
                        sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no backend/nginx "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/backend/nginx"

                        # Frontend Dockerfile
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no frontend/Dockerfile "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/frontend/Dockerfile"
                    '''
                }
            }
        }

        stage('Deploy Backend on Remote Server') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$DEPLOY_HOST "cd /opt/deployment/backend && docker-compose pull && docker-compose up -d"
                    '''
                }
            }
        }

        stage('Deploy Frontend on Remote Server') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$DEPLOY_HOST "cd /opt/deployment/frontend && docker pull $FRONTEND_IMAGE:$IMAGE_TAG && docker stop frontend-container || true && docker rm frontend-container || true && docker run -d --name frontend-container -p 3000:3000 $FRONTEND_IMAGE:$IMAGE_TAG"
                    '''
                }
            }
        }
    }
}
