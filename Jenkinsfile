@Library('Shared') _

pipeline {
    agent { label 'BuildBot' }

    stages {

        stage('Code Clone') {
            steps {
                clone("https://github.com/hdarji1912/todo-app.git", "main")
            }
        }

        stage('Build Docker Image') {
            steps {
                dockerbuild("darjihardik", "todo-app", "latest")
            }
        }

        stage('Push to DockerHub') {
            steps {
                dockerpush("dockerHubCreds", "todo-app", "latest")
            }
        }

        stage('Deploy') {
            steps {
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
                to: 'hdarji783@gmail.com',
                subject: 'Build Successful',
                body: 'Pipeline completed successfully.'
            )
        }

        failure {
            emailext(
                to: 'hdarji783@gmail.com',
                subject: 'Build Failed',
                body: 'Pipeline execution failed.'
            )
        }
    }
}
