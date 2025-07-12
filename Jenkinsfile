pipeline {
    agent any

    environment {
        BACKEND_REPO  = 'https://github.com/Med-X9/InventaireModuleWMS.git'
        IMAGE_PREFIX = 'oussamafannouch'
        BACKEND_IMAGE  = "${IMAGE_PREFIX}/backend-app"
        IMAGE_TAG = "latest"
        DEPLOY_HOST = '147.93.55.221'
        DEPLOY_USER = credentials('dev-test-creds') 
    }

    stages {
        stage('Check Branch') {
            steps {
                script {
                    if (env.BRANCH_NAME != 'dev') {
                        echo "Skipping deployment - not on dev branch. Current branch: ${env.BRANCH_NAME}"
                        currentBuild.result = 'SUCCESS'
                        return
                    }
                    echo "Proceeding with deployment on dev branch"
                }
            }
        }

        stage('Clone Repositories') {
            when {
                branch 'dev'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'git-cred', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                    sh '''
                        rm -rf /tmp/backend
                        git clone --single-branch --branch dev https://$GIT_USER:$GIT_PASS@github.com/Med-X9/InventaireModuleWMS.git /tmp/backend
                    '''
                }
            }
        }

        stage('Build Backend Docker Image') {
            when {
                branch 'dev'
            }
            steps {
                dir('/tmp/backend') {
                    sh 'docker build -t $BACKEND_IMAGE:$IMAGE_TAG .'
                }
            }
        }

        stage('Push Docker Images') {
            when {
                branch 'dev'
            }
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
            when {
                branch 'dev'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "rm -rf /tmp/deployment/backend && mkdir -p /tmp/deployment/backend"
                        sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no /tmp/backend/. "$USER@$DEPLOY_HOST:/tmp/deployment/backend/"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no "/tmp/backend/.env copy" "$USER@$DEPLOY_HOST:/tmp/deployment/backend/.env"
                    '''
                }
            }
        }

        stage('Deploy Backend on Remote Server') {
            when {
                branch 'dev'
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dev-test-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh root@147.93.55.221 "bash -c 'cd /tmp/deployment/backend && docker-compose pull && docker-compose up -d'"
                    '''
                }
            }
        }
    }

    post {
        success {
            script {
                if (env.BRANCH_NAME == 'dev') {
                    echo "✅ Deployment to dev environment completed successfully!"
                } else {
                    echo "✅ Pipeline completed - no deployment needed for branch: ${env.BRANCH_NAME}"
                }
            }
        }
        failure {
            echo "❌ Pipeline failed!"
        }
    }
}