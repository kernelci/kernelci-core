
This directory contains Jenkins shared libraries to be used by kernelci.org.
Please, DO NOT REMOVE, MOVE OR RENAME this directory without checking first
because it will break Jenkinsfiles using these libraries.

These libraries can be used importing them in the top of the Jenkinsfile:

```
library identifier: 'REPO_NAME@BRANCH', retriever: modernSCM(
  [$class: 'GitSCMSource',
   remote: 'http://github.com/kernelci/REPO_NAME'])
```

where `REPO_NAME` is the repository name and `BRANCH` is the branch of the repository.

Or they can be declared in Jenkins globally, as exlpained in this article:
https://dev.to/jalogut/centralise-jenkins-pipelines-configuration-using-shared-libraries


You can read more about shared libraries at https://jenkins.io/doc/book/pipeline/shared-libraries/
