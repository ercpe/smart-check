node('docker') {

    stage('Checkout') {
        git 'https://git.ercpe.de/ercpe/smart-check.git'
    }

    stage('CI') {
        docker.withRegistry('https://r.ercpe.de', 'docker-registry') {
            docker.image('r.ercpe.de/ercpe/python-build:latest').inside {
                sh "make jenkins"
            }
        }
    }

    stage('Debian packaging') {
        docker.withRegistry('https://r.ercpe.de', 'docker-registry') {
            def build = docker.image('r.ercpe.de/ercpe/ubuntu-build:latest');

            // https://github.com/jenkinsci/docker-workflow-plugin/pull/57
            build.inside('--user root:root') {
                sh "apt update && apt install -y dh-python python3-all python3-setuptools"
            }
            build.inside {
                sh "make deb"
            }
        }
    }

}
