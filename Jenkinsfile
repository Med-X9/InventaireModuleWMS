pipeline {
    agent any

    tools {
        // Ensure SonarQube Scanner is available
        'org.sonarsource.scanner.jenkins.tool.SonarRunnerInstallation' 'sonar-scanner'
    }

    environment {
        FRONTEND_REPO = 'https://github.com/Med-X9/inventaireModuleWMSFront.git'
        BACKEND_REPO  = 'https://github.com/Med-X9/InventaireModuleWMS.git'

        IMAGE_PREFIX = 'oussamafannouch'
        FRONTEND_IMAGE = "${IMAGE_PREFIX}/frontend-app"
        BACKEND_IMAGE  = "${IMAGE_PREFIX}/backend-app"
        IMAGE_TAG = "latest"

        DEPLOY_HOST = '167.99.219.120'
        DEPLOY_USER = credentials('devops-creds')
        
        // SonarQube configuration
        SONAR_PROJECT_KEY = 'inventaire-module-wms'
        SONAR_PROJECT_NAME = 'InventaireModuleWMS'
        SONAR_PROJECT_VERSION = '1.0'
    }

    stages {
        stage('Check Branch') {
            steps {
                script {
                    echo "Building branch: ${env.BRANCH_NAME ?: 'devops'}"
                    echo "Commit: ${env.GIT_COMMIT ?: 'N/A'}"
                }
            }
        }

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

        stage('SonarQube Analysis') {
            when {
                anyOf {
                    branch 'main'
                    branch 'devops'
                    branch 'dev'
                }
            }
            steps {
                dir('/tmp/backend') {
                    script {
                        try {
                            // Install Python dependencies for testing (optional)
                            sh '''
                                echo "Setting up Python environment..."
                                python3 -m pip install --user -r requirements.txt || echo "Warning: Failed to install some dependencies, continuing with analysis..."
                            '''
                        } catch (Exception e) {
                            echo "Warning: Python setup failed, but continuing with SonarQube analysis: ${e.getMessage()}"
                        }
                        
                        // Run SonarQube analysis
                        withSonarQubeEnv('SonarQube-Server') {
                            sh """
                                echo "Starting SonarQube analysis..."
                                sonar-scanner \\
                                    -Dsonar.projectKey=${SONAR_PROJECT_KEY} \\
                                    -Dsonar.projectName="${SONAR_PROJECT_NAME}" \\
                                    -Dsonar.projectVersion=${SONAR_PROJECT_VERSION} \\
                                    -Dsonar.sources=apps,project,config \\
                                    -Dsonar.sourceEncoding=UTF-8 \\
                                    -Dsonar.language=py \\
                                    -Dsonar.python.version=3.12 \\
                                    -Dsonar.tests=apps \\
                                    -Dsonar.test.inclusions="**/tests/**/*.py,**/test_*.py" \\
                                    -Dsonar.exclusions="**/migrations/**,**/staticfiles/**,**/static/**,**/media/**,**/__pycache__/**,**/venv/**,**/env/**,**/node_modules/**,**/*.pyc,**/manage.py,**/wsgi.py,**/asgi.py,**/settings/**,**/*.min.js,**/*.min.css" \\
                                    -Dsonar.coverage.exclusions="**/migrations/**,**/tests/**,**/test_*.py,**/conftest.py,**/manage.py,**/wsgi.py,**/asgi.py,**/settings/**,**/__init__.py" \\
                                    -Dsonar.cpd.exclusions="**/migrations/**,**/tests/**" \\
                                    -Dsonar.qualitygate.wait=true
                                echo "SonarQube analysis completed."
                            """
                        }
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: false
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
                withCredentials([usernamePassword(credentialsId: 'devops-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "rm -rf /tmp/deployment/backend && mkdir -p /tmp/deployment/backend"
                        sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "mkdir -p /tmp/deployment/frontend"

                        sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no /tmp/backend/. "$USER@$DEPLOY_HOST:/tmp/deployment/backend/"
                        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/.env.prod "$USER@$DEPLOY_HOST:/tmp/deployment/backend/.env"

                    '''
                }
            }
        }


        stage('Deploy Backend on Remote Server') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'devops-creds', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        sshpass -p "$PASS" ssh root@147.93.55.221 "bash -c 'cd /tmp/deployment/backend && docker-compose pull && docker-compose up -d'"
                    '''
                }
            }
        }
    }

    post {
        always {
            // Clean up workspace
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
            echo 'SonarQube analysis results: Check http://your-sonar-server:9000/dashboard?id=inventaire-module-wms'
        }
        failure {
            echo 'Pipeline failed!'
        }
        unstable {
            echo 'Pipeline completed with warnings. Check SonarQube Quality Gate results.'
        }
    }
}
