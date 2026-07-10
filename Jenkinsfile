@Library('Shared')_
pipeline{
    agent { label 'BuildBot'}
    
    stages{
        stage("Code clone"){
            steps{
                sh "whoami"
            clone("https://github.com/hdarji1912/todo-app.git","main")
            }
        }
        stage("Code Build"){
            steps{
            dockerbuild("todo-app","latest")
            }
        }
        stage("Push to DockerHub"){
            steps{
                dockerpush("dockerHubCreds","todo-app","latest")
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
        stage("Deploy"){
            steps{
                deploy()
            }
        }
      }
        
    }
}