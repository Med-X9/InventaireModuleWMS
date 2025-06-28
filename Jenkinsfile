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
        DOCKER_COMPOSE_DIR = '/tmp/deployment'

        LOCAL_CLONE_DIR = '/tmp'
    }

    stages {
        stage('Clone Repositories') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'git-cred', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                    sh '''
                        rm -rf $LOCAL_CLONE_DIR/frontend $LOCAL_CLONE_DIR/backend
                        git clone https://$GIT_USER:$GIT_PASS@github.com/Med-X9/InventaireModuleWMS.git $LOCAL_CLONE_DIR/backend
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
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p $DOCKER_COMPOSE_DIR/backend"
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p $DOCKER_COMPOSE_DIR/frontend"

                        # Backend uploads
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no $LOCAL_CLONE_DIR/backend/docker-compose.yml "$USER@$DEPLOY_HOST:/tmp/deployment/docker-compose.yml"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no $LOCAL_CLONE_DIR/backend/Dockerfile "$USER@$DEPLOY_HOST:/tmp/deployment/Dockerfile"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no $LOCAL_CLONE_DIR/backend/.env.prod "$USER@$DEPLOY_HOST:/tmp/deployment/.env.prod"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no $LOCAL_CLONE_DIR/backend/requirements.txt "$USER@$DEPLOY_HOST:/tmp/deployment/requirements.txt"
                        sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no $LOCAL_CLONE_DIR/backend/nginx "$USER@$DEPLOY_HOST:/tmp/deployment/nginx"

                    '''
                }
            }
        }

        stage('Deploy Backend on Remote Server') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$DEPLOY_HOST "cd /tmp/deployment/backend && docker-compose pull && docker-compose up -d"
                    '''
                }
            }
        }
    }
}
