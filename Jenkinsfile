@Library('Shared') _

pipeline {
    agent { label 'BuildBot' }

    stages {

        stage('Code Clone') {
            steps {
                echo "Cloning GitHub Repository..."
                clone(
                    "https://github.com/hdarji1912/todo-app.git",
                    "main"
                )
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker Image..."
                dockerbuild(
                    "darjihardik",
                    "todo-app",
                    "latest"
                )
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo "Pushing Docker Image..."
                dockerpush(
                    "dockerHubCreds",
                    "todo-app",
                    "latest"
                )
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying Application..."
                deploy(
                    "darjihardik",
                    "todo-app",
                    "latest",
                    "todo-app",
                    "5000",
                    "5000"
                )
            }
        }
    }

    post {

        success {
            emailext(
                from: 'hdarji783@gmail.com',
                to: 'hdarji783@gmail.com',
                subject: '✅ Jenkins Pipeline Success',
                body: '''
Hello,

Your Jenkins pipeline completed successfully.

Stages Completed:
✔ Code Clone
✔ Docker Build
✔ Docker Push
✔ Deploy

Regards,
Jenkins
'''
            )
        }

        failure {
            emailext(
                from: 'hdarji783@gmail.com',
                to: 'hdarji783@gmail.com',
                subject: '❌ Jenkins Pipeline Failed',
                body: '''
Hello,

Your Jenkins pipeline has failed.

Please check the Jenkins Console Output for more details.

Regards,
Jenkins
'''
            )
        }
    }
}
