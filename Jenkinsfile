pipeline {
    agent any

    environment {
        IMAGE_PREFIX = 'oussamafannouch'
        FRONTEND_IMAGE = "${IMAGE_PREFIX}/frontend-app"
        BACKEND_IMAGE  = "${IMAGE_PREFIX}/backend-app"
        IMAGE_TAG = "latest"

        DEPLOY_HOST = '147.93.55.221'
        DOCKER_COMPOSE_DIR = '/opt/deployment'
    }

    stages {
        stage('Build Frontend Docker Image') {
            steps {
                sh 'docker build -t $FRONTEND_IMAGE:$IMAGE_TAG /tmp/frontend'
            }
        }

        stage('Build Backend Docker Image') {
            steps {
                sh 'docker build -t $BACKEND_IMAGE:$IMAGE_TAG /tmp/backend'
            }
        }

        stage('Push Docker Images') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', passwordVariable: 'PASS', usernameVariable: 'USER')]) {
                    sh '''
                        echo "$PASS" | docker login -u "$USER" --password-stdin
                        docker push $FRONTEND_IMAGE:$IMAGE_TAG
                        docker push $BACKEND_IMAGE:$IMAGE_TAG
                    '''
                }
            }
        }

        stage('Uploading Files') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p $DOCKER_COMPOSE_DIR/frontend"
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p $DOCKER_COMPOSE_DIR/backend"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/docker-compose.yml "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/backend/docker-compose.yml"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/Dockerfile "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/backend/Dockerfile"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/.env "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/backend/.env"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/frontend/Dockerfile "$USER@$DEPLOY_HOST:$DOCKER_COMPOSE_DIR/frontend/Dockerfile"
                    '''
                }
            }
        }

        stage('Deploy Backend on Remote Server') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" << EOF
                        cd $DOCKER_COMPOSE_DIR/backend
                        docker-compose pull
                        docker-compose up -d
                        EOF
                    '''
                }
            }
        }

        stage('Deploy Frontend on Remote Server') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" << EOF
                        cd $DOCKER_COMPOSE_DIR/frontend
                        docker pull $FRONTEND_IMAGE:$IMAGE_TAG
                        docker stop frontend-container || true
                        docker rm frontend-container || true
                        docker run -d --name frontend-container -p 3000:3000 $FRONTEND_IMAGE:$IMAGE_TAG
                        EOF
                    '''
                }
            }
        }
    }
}
