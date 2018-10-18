#!/usr/bin/env sh
set -v

pip install -r test_requirements.txt

export COMMIT_MSG=$(git show HEAD^2 -s || git show HEAD -s)

cd .. && git clone https://github.com/pulp/pulp.git

# When building for a release tag, let the pip install of pulp_cookbook
# below work out the dependencies using published PyPi packages, otherwise
# install the development versions of the Pulp modules
if [ -z "$TRAVIS_TAG" ]; then
  export PULP_PR_NUMBER=$(echo $COMMIT_MSG | grep -oP 'Required\ PR:\ https\:\/\/github\.com\/pulp\/pulp\/pull\/(\d+)' | awk -F'/' '{print $7}')

  if [ -n "$PULP_PR_NUMBER" ]; then
    pushd pulp
    git fetch origin +refs/pull/$PULP_PR_NUMBER/merge
    git checkout FETCH_HEAD
    popd
  fi

  pushd pulp/pulpcore/ && pip install -e . && popd
  pushd pulp/plugin/ && pip install -e .  && popd

fi

cd pulp_cookbook
pip install -e .
