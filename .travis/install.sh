#!/usr/bin/env sh
set -v

pip install -r test_requirements.txt

export COMMIT_MSG=$(git show HEAD^2 -s || git show HEAD -s)

cd ..

# When building for a release tag, let the pip install of pulp_cookbook
# below work out the dependencies using published PyPI packages, otherwise
# install the development versions of the Pulp modules
if [ -z "$TRAVIS_TAG" ]; then
  export PULP_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/pulp\/pulpcore\/pull\/(\d+)' | awk -F'/' '{print $7}')
  export PULP_PLUGIN_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/pulp\/pulpcore-plugin\/pull\/(\d+)' | awk -F'/' '{print $7}')

  git clone --depth 1 https://github.com/pulp/pulpcore.git
  if [ -n "$PULP_PR_NUMBER" ]; then
    pushd pulpcore
    git fetch origin +refs/pull/$PULP_PR_NUMBER/merge
    git checkout FETCH_HEAD
    popd
  fi

  pip install -e ./pulpcore[postgres]

  git clone --depth 1 https://github.com/pulp/pulpcore-plugin.git
  if [ -n "$PULP_PLUGIN_PR_NUMBER" ]; then
    pushd pulpcore-plugin
    git fetch origin +refs/pull/$PULP_PLUGIN_PR_NUMBER/merge
    git checkout FETCH_HEAD
    popd
  fi

  pip install -e ./pulpcore-plugin
fi

cd pulp_cookbook
pip install -e .
