pipeline {
    agent any
    environment {
        DOCKER_IMAGE = 'antifraude-demo'
        REGISTRY = 'localhost:5000'  // Registro local
        SONAR_SCANNER_HOME = tool 'SonarQubeScanner'
    }
    
    stages {
        // Etapa 1: Checkout del código
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/criptomoney0101/antifraude-demo.git'
                echo "Código fuente obtenido de GitHub"
            }
        }
        
        // Etapa 2: Análisis estático con SonarQube
        stage('SonarQube Analysis') {
            steps {
                script {
                    withSonarQubeEnv('SonarQube') {
                        sh "${SONAR_SCANNER_HOME}/bin/sonar-scanner"
                    }
                }
            }
        }
        
        // Etapa 3: Verificación de Quality Gate
        stage('Quality Gate') {
            steps {
                script {
                    timeout(time: 5, unit: 'MINUTES') {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline abortado por fallo en Quality Gate: ${qg.status}"
                        }
                    }
                }
            }
        }
        
        // Etapa 4: Construcción de imagen Docker
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${env.BUILD_ID}")
                    echo "Imagen Docker construida: ${DOCKER_IMAGE}:${env.BUILD_ID}"
                }
            }
        }
        
        // Etapa 5: Ejecución de pruebas unitarias
        stage('Run Tests') {
            steps {
                script {
                    docker.image("${DOCKER_IMAGE}:${env.BUILD_ID}").inside {
                        sh 'python -m pytest tests/ --cov=. --cov-report=xml --junitxml=report.xml'
                    }
                }
                publishTestResults testResultsPattern: 'report.xml'
                publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
            }
        }
        
        // Etapa 6: Escaneo de seguridad en imagen Docker
        stage('Security Scan') {
            steps {
                script {
                    // Usamos comillas simples para evitar la interpolación de variables de Groovy
                    sh '''
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                    -v $(pwd):/root/.cache/ aquasec/trivy image --exit-code 0 --severity HIGH,CRITICAL ''' + "${DOCKER_IMAGE}:${env.BUILD_ID}" + '''
                    '''
                }
            }
        }
        
        // Etapa 7: Push al registro local
        stage('Push to Registry') {
            steps {
                script {
                    docker.withRegistry("http://${REGISTRY}") {
                        docker.image("${DOCKER_IMAGE}:${env.BUILD_ID}").push()
                    }
                    echo "Imagen push al registro local: ${REGISTRY}/${DOCKER_IMAGE}:${env.BUILD_ID}"
                }
            }
        }
        
        // Etapa 8: Despliegue en Staging
        stage('Deploy to Staging') {
            steps {
                script {
                    // Detener contenedor anterior si existe
                    sh 'docker stop antifraude-staging || true'
                    sh 'docker rm antifraude-staging || true'
                    
                    // Ejecutar nuevo contenedor
                    sh '''
                    docker run -d \
                    --name antifraude-staging \
                    -p 5001:5000 \
                    -e ENVIRONMENT=staging \
                    ''' + "${REGISTRY}/${DOCKER_IMAGE}:${env.BUILD_ID}" + '''
                    '''
                    
                    echo "Aplicación desplegada en staging (puerto 5001)"
                }
            }
        }
        
        // Etapa 9: Pruebas de humo (Smoke Tests)
        stage('Smoke Tests') {
            steps {
                script {
                    // Esperar a que la aplicación inicie
                    sleep(time: 10, unit: 'SECONDS')
                    
                    // Prueba de health check
                    sh 'curl -f http://localhost:5001/health || exit 1'
                    
                    // Prueba de transacción válida
                    sh '''
                    curl -X POST http://localhost:5001/validate \
                    -H "Content-Type: application/json" \
                    -d '{"amount": 500, "card_number": "4222222222222222", "country": "AR"}' | \
                    jq -e '.status == "APPROVED"' || exit 1
                    '''
                    
                    // Prueba de transacción rechazada
                    sh '''
                    curl -X POST http://localhost:5001/validate \
                    -H "Content-Type: application/json" \
                    -d '{"amount": 1500, "card_number": "4222222222222222", "country": "AR"}' | \
                    jq -e '.status == "REJECTED"' || exit 1
                    '''
                    
                    echo "Pruebas de humo superadas"
                }
            }
        }
    }
    
    // Acciones post-ejecución
    post {
        always {
            echo 'Pipeline finalizado. Limpiando recursos...'
            sh 'docker image prune -f'
            cleanWs()
        }
        success {
            echo 'Pipeline ejecutado exitosamente'
            // Notificación a Slack (opcional)
            // slackSend channel: '#devops', message: "Pipeline exitoso: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        failure {
            echo 'Pipeline fallido. Revisar logs.'
            // Notificación a Slack (opcional)
            // slackSend channel: '#devops', color: 'danger', message: "Pipeline fallido: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
    }
}
