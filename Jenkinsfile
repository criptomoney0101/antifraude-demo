ipeline {
    agent any
    environment {
        DOCKER_IMAGE = 'antifraude-demo'
        REGISTRY = 'localhost:5000'  // Registro local
    }
    
    stages {
        // Etapa 1: Checkout del código
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/criptomoney0101/antifraude-demo.git'
                echo "Código fuente obtenido de GitHub"
            }
        }
        
        // Etapa 2: Verificar entorno
        stage('Verify Environment') {
            steps {
                script {
                    // Verificar Docker
                    sh 'docker --version'
                    
                    // Verificar conexión a SonarQube
                    sh 'curl -f http://sonarqube:9000/api/system/status || echo "SonarQube no accesible, usando URL alternativa"'
                }
            }
        }
        
        // Etapa 3: Análisis estático con SonarQube
        stage('SonarQube Analysis') {
            steps {
                script {
                    // Usar el scanner directamente
                    withSonarQubeEnv('SonarQube') {
                        sh 'sonar-scanner -Dsonar.projectKey=antifraude-demo -Dsonar.sources=. -Dsonar.host.url=http://sonarqube:9000'
                    }
                }
            }
        }
        
        // Etapa 4: Verificación de Quality Gate
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
        
        // Etapa 5: Construcción de imagen Docker
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${env.BUILD_ID}")
                    echo "Imagen Docker construida: ${DOCKER_IMAGE}:${env.BUILD_ID}"
                }
            }
        }
        
        // Etapa 6: Ejecución de pruebas unitarias
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
        
        // Etapa 7: Escaneo de seguridad en imagen Docker
        stage('Security Scan') {
            steps {
                script {
                    sh '''
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                    -v $(pwd):/root/.cache/ aquasec/trivy image --exit-code 0 --severity HIGH,CRITICAL ''' + "${DOCKER_IMAGE}:${env.BUILD_ID}" + '''
                    '''
                }
            }
        }
        
        // Etapa 8: Push al registro local
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
        
        // Etapa 9: Despliegue en Staging
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
        
        // Etapa 10: Pruebas de humo (Smoke Tests)
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
            script {
                try {
                    echo 'Pipeline finalizado. Limpiando recursos...'
                    sh 'docker image prune -f'
                    cleanWs()
                } catch (Exception e) {
                    echo "Error durante la limpieza: ${e.getMessage()}"
                }
            }
        }
        success {
            echo 'Pipeline ejecutado exitosamente'
        }
        failure {
            echo 'Pipeline fallido. Revisar logs.'
        }
    }
}
