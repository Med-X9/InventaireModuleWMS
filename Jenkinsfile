pipeline {
    agent any

    environment {
        BACKEND_REPO  = 'https://github.com/Med-X9/InventaireModuleWMS.git'
        IMAGE_PREFIX = 'smatchdigital'
        BACKEND_IMAGE  = "${IMAGE_PREFIX}/backend-app"
        IMAGE_TAG = "latest"
        
        // Deployment configuration
        DEPLOY_HOST  = "${env.BRANCH_NAME == 'main' ? '31.97.158.68' : (env.BRANCH_NAME == 'dev' ? '147.93.55.221' : '')}"
        DEPLOY_CREDS = "${env.BRANCH_NAME == 'main' ? 'prod-creds' : (env.BRANCH_NAME == 'dev' ? 'dev-test-creds' : '')}"
        ENV_NAME     = "${env.BRANCH_NAME == 'main' ? 'production' : (env.BRANCH_NAME == 'dev' ? 'development' : '')}"
        
        // SonarQube
        SONAR_PROJECT_KEY = "inventaire-module-wms-${env.BRANCH_NAME}"
        SONAR_PROJECT_NAME = "InventaireModuleWMS-${env.BRANCH_NAME}"
        SONAR_PROJECT_VERSION = '1.0'
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

        stage('SonarQube Analysis') {
            environment {
                scannerHome = tool 'sonar-scanner'
            }
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
                        withSonarQubeEnv(credentialsId: 'sonar-token', installationName: 'SonarQube-Server') {
                            sh """
                                echo "Starting SonarQube analysis for branch: ${env.BRANCH_NAME}"
                                \${scannerHome}/bin/sonar-scanner \\
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
                                echo "SonarQube analysis completed for branch: ${env.BRANCH_NAME}"
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
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-company', passwordVariable: 'PASS', usernameVariable: 'USER')]) {
                        sh "echo $PASS | docker login -u $USER --password-stdin"
                    }
                    def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                    sh "docker push ${BACKEND_IMAGE}:${imageTag}"
                    sh "docker push ${BACKEND_IMAGE}:${IMAGE_TAG}"
                }
            }
        }

        stage('Upload Essential Files') {
            when {
                anyOf {
                    branch 'dev'
                    branch 'main'
                }
            }
            steps {
                script {
                    def imageTag = env.BRANCH_NAME == 'main' ? 'prod-latest' : 'dev-latest'
                    echo "Preparing deployment files for ${env.ENV_NAME} environment with image: ${BACKEND_IMAGE}:${imageTag}"
                    
                    if (!env.DEPLOY_CREDS) {
                        error("DEPLOY_CREDS environment variable is not set!")
                    }
                    if (!env.DEPLOY_HOST) {
                        error("DEPLOY_HOST environment variable is not set!")
                    }
                    
                    withCredentials([usernamePassword(credentialsId: env.DEPLOY_CREDS, usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        sh '''
                            # Create deployment directory on remote server
                            sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no "$USER@$DEPLOY_HOST" "rm -rf /tmp/deployment/backend && mkdir -p /tmp/deployment/backend/nginx"
                            
                            # Upload only essential files
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/docker-compose.yml "$USER@$DEPLOY_HOST:/tmp/deployment/backend/"
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/backend/Dockerfile "$USER@$DEPLOY_HOST:/tmp/deployment/backend/"
                            sshpass -p "$PASS" scp -r -o StrictHostKeyChecking=no /tmp/backend/nginx/* "$USER@$DEPLOY_HOST:/tmp/deployment/backend/nginx/"
                            sshpass -p "$PASS" scp -o StrictHostKeyChecking=no "/tmp/backend/.env copy" "$USER@$DEPLOY_HOST:/tmp/deployment/backend/.env"
                        '''
                        
                        // Create .env file with IMAGE_TAG variable on remote server
                        sh """
                            sshpass -p "\$PASS" ssh -o StrictHostKeyChecking=no "\$USER@\$DEPLOY_HOST" "
                                cd /tmp/deployment/backend &&
                                echo 'IMAGE_TAG=${imageTag}' >> .env &&
                                echo 'Added IMAGE_TAG=${imageTag} to .env file'
                            "
                        """
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
                    if (!env.DEPLOY_CREDS) {
                        error("DEPLOY_CREDS environment variable is not set!")
                    }
                    if (!env.DEPLOY_HOST) {
                        error("DEPLOY_HOST environment variable is not set!")
                    }
                    
                    withCredentials([usernamePassword(credentialsId: env.DEPLOY_CREDS, usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        sh '''
                            sshpass -p "$PASS" ssh "$USER@$DEPLOY_HOST" "bash -c 'cd /tmp/deployment/backend && docker-compose down -v && docker-compose pull && docker-compose up -d'"
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                // Clean up temporary files
                sh '''
                    rm -rf /tmp/backend || true
                    docker system prune -f || true
                '''
            }
        }
        success {
            script {
                if (env.BRANCH_NAME == 'dev') {
                    echo "✅ Successfully deployed to development environment (${env.DEPLOY_HOST})!"
                    echo "🐳 Using image: ${env.BACKEND_IMAGE}:dev-latest"
                    def projectKey = "inventaire-module-wms-${branchName}"
                    echo "SonarQube analysis results for ${branchName}: http://147.93.55.221:9000/dashboard?id=${projectKey}"
                } else if (env.BRANCH_NAME == 'main') {
                    echo "✅ Successfully deployed to production environment (${env.DEPLOY_HOST})!"
                    echo "🐳 Using image: ${env.BACKEND_IMAGE}:prod-latest"
                    def projectKey = "inventaire-module-wms-${branchName}"
                    echo "SonarQube analysis results for ${branchName}: http://147.93.55.221:9000/dashboard?id=${projectKey}"
                } else {
                    echo "✅ Pipeline completed - no deployment needed for branch: ${env.BRANCH_NAME}"
                }
                echo "📁 Transferred files: docker-compose.yml, nginx/, .env"
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
        unstable {
            echo 'Pipeline completed with warnings. Check SonarQube Quality Gate results.'
        }
    }
}
