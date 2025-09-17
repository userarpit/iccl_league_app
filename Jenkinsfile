pipeline {
    agent any
    
    environment {
        VENV = "venv"
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    checkout scm
                }
            }
        }
        stage('Setup Python Environment') {
            steps {
                sh '''
                python3 -m venv $VENV
                . $VENV/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Unit & Integration Tests') {
            steps {
                sh '''
                . $VENV/bin/activate
                python iccl_league_app/manage.py test league.tests --settings=iccl_league_app.settings_test
                '''
            }
        }

        stage('Database Migration Check') {
            steps {
                sh '''
                . $VENV/bin/activate
                python iccl_league_app/manage.py makemigrations --check --dry-run
                python iccl_league_app/manage.py migrate --plan
                '''
            }
        }

        stage('Linting & Code Quality') {
            steps {
                sh '''
                . $VENV/bin/activate
                black .
                flake8 .
                '''
            }
        }

    }

    post {
        // always {
        //     junit '/test-results.xml' // if using pytest with --junitxml
        //     archiveArtifacts artifacts: '/coverage.xml', allowEmptyArchive: true
        // }
        failure {
            mail to: 'masterarpit@gmail.com',
                 subject: "Build Failed in Jenkins: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: "Check Jenkins for details."
        }
    }
}