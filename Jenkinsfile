// Jenkins Pipeline - autotest 对接
// 前置: Jenkins 装 "JUnit Plugin"（默认随附）。LLM key 用 "Managed Credentials" 存为 rcc-llm-key
pipeline {
    agent any
    options { timestamps(); timeout(time: 30, unit: 'MINUTES') }
    parameters {
        string(name: 'BASE_URL', defaultValue: 'http://10.x.x.x:8080',
               description: 'RCC-Space 测试环境地址')
        string(name: 'CASE_DIR', defaultValue: 'cases', description: '用例目录')
        string(name: 'LLM_MODEL', defaultValue: 'deepseek-chat', description: 'LLM 模型')
        booleanParam(name: 'NO_CACHE', defaultValue: false,
                     description: '勾选则禁用 plan 缓存（强制重新调 LLM 编排）')
    }
    environment {
        // CI 凭据注入：环境变量覆盖 model_config.json 的 api_key（不进仓库）
        LLM_API_KEY = credentials('rcc-llm-key')
        LLM_MODEL   = "${params.LLM_MODEL}"
    }
    stages {
        stage('Setup') {
            steps {
                sh 'python3 -m pip install -r requirements.txt -q'
                sh 'python3 -c "from app.core import get_index; n=len(get_index().load()); print(f\\"接口数 {n}\\")"'
                // 回归测试：编排/规则库/文档（不依赖真实环境与 LLM；失败即中止，防止带回归进入真实用例）
                sh 'python3 tests/test_orchestration.py'
                // 运行配置(global_params.yaml)不入库:CI 缺失时生成最小模板,凭据走环境变量 TEST_ADMIN_USER/TEST_ADMIN_PASSWORD
                sh 'mkdir -p app/data && [ -f app/data/global_params.yaml ] || echo "base_url: \${BASE_URL}\nrcdc_user:\nrcdc_passwd:" > app/data/global_params.yaml'
            }
        }
        stage('Test') {
            steps {
                sh """
                    python3 run_cases.py ${CASE_DIR} \
                      --params app/data/global_params.yaml \
                      --base-url ${BASE_URL} \
                      --llm-config app/data/model_config.json \
                      --junit report.xml \
                      ${NO_CACHE ? '--no-cache' : ''}
                """
            }
        }
    }
    post {
        always {
            // Jenkins 解析 JUnit 并在构建页展示红绿/趋势图
            junit testResults: 'report.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'report.xml', allowEmptyArchive: true
        }
    }
}
