pipeline {
    agent any

    stages {
        stage("code clone") {
            steps {
                git url: "https://github.com/hdarji1912/todo-app.git", branch: "main"
                echo "Code clone successfully hurray ..!"
            }
        }
        stage("trivy scan step"){
            steps{
                sh "trivy fs . -o results.json"
            }
        }
        stage("docker build") {
            steps {
                sh "docker build -t my-app ."
                echo "docker build successfully..!"
            }
        }

        stage("DockerHub Push") {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhubcred',
                    usernameVariable: 'DockerHubUser',
                    passwordVariable: 'DockerHubPass'
                )]) {
                    sh '''
                      echo "$DockerHubPass" | docker login -u "$DockerHubUser" --password-stdin
                      docker tag my-app $DockerHubUser/my-app:latest
                      docker push $DockerHubUser/my-app:latest
                    '''
                }
            }
        }

        stage("docker compose") {
            steps {
                sh "docker compose up -d"
                echo "Docker container is Up & Running..!"
            }
        }
    }

    post {
        success {
            emailext(
                from: 'hdarji783@gmail.com',
                to: 'hdarji783@gmail.com',
                subject: '✅ build success',
                body: '✅ build success'
            )
        }

        failure {
            emailext(
                from: 'hdarji783@gmail.com',
                to: 'hdarji783@gmail.com',
                subject: '❌ build failed',
                body: '❌ build failed'
            )
        }
    }
}