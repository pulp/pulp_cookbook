#!/bin/bash

SNIPPET_DIR=../_snippets

source base.sh

set -o errexit -o nounset
set -x

unset REPO_HREF
source create_repo_foo.sh > ${SNIPPET_DIR}/create_repo_foo.txt
echo >> ${SNIPPET_DIR}/create_repo_foo.txt

if [[ ! -f ubuntu-2.0.1.tgz ]]; then
    curl -Lo ubuntu-2.0.1.tgz https://supermarket.chef.io:443/api/v1/cookbooks/ubuntu/versions/2.0.1/download
fi
if [[ ! -f apt-7.0.0.tgz ]]; then
    curl -Lo apt-7.0.0.tgz https://supermarket.chef.io:443/api/v1/cookbooks/apt/versions/7.0.0/download
fi

source create_content_ubuntu.sh > ${SNIPPET_DIR}/create_content_ubuntu.txt
echo >> ${SNIPPET_DIR}/create_content_ubuntu.txt

source create_content_apt.sh > ${SNIPPET_DIR}/create_content_apt.txt
echo >> ${SNIPPET_DIR}/create_content_apt.txt

source add_content_to_repo.sh > ${SNIPPET_DIR}/add_content_to_repo.txt
echo >> ${SNIPPET_DIR}/add_content_to_repo.txt

source delete_repo_foo.sh > ${SNIPPET_DIR}/delete_repo_foo.txt
echo >> ${SNIPPET_DIR}/delete_repo_foo.txt

source create_remote_foo.sh > ${SNIPPET_DIR}/create_remote_foo.txt
echo >> ${SNIPPET_DIR}/create_remote_foo.txt

source create_repo_foo_with_remote.sh > ${SNIPPET_DIR}/create_repo_foo_with_remote.txt
echo >> ${SNIPPET_DIR}/create_repo_foo_with_remote.txt

source sync_repo_foo.sh > ${SNIPPET_DIR}/sync_repo_foo.txt
echo >> ${SNIPPET_DIR}/sync_repo_foo.txt

source get_latest_version_foo.sh > ${SNIPPET_DIR}/get_latest_version_foo.txt
echo >> ${SNIPPET_DIR}/get_latest_version_foo.txt

source create_publication_foo.sh > ${SNIPPET_DIR}/create_publication_foo.txt
echo >> ${SNIPPET_DIR}/create_publication_foo.txt

source create_distribution_foo.sh > ${SNIPPET_DIR}/create_distribution_foo.txt
echo >> ${SNIPPET_DIR}/create_distribution_foo.txt

source get_universe_foo.sh > ${SNIPPET_DIR}/get_universe_foo.txt
echo >> ${SNIPPET_DIR}/get_universe_foo.txt

sudo dnf -y install ruby ruby-devel redhat-rpm-config
gem install berkshelf
rm -rf ~/.berkshelf/ Berksfile.lock

source berks_install_foo.sh > ${SNIPPET_DIR}/berks_install_foo.txt

# Lazy Cookbook Sync

source create_remote_supermarket.sh > ${SNIPPET_DIR}/create_remote_supermarket.txt
echo >> ${SNIPPET_DIR}/create_remote_supermarket.txt

source create_repo_supermarket.sh > ${SNIPPET_DIR}/create_repo_supermarket.txt
echo >> ${SNIPPET_DIR}/create_repo_supermarket.txt

source sync_repo_supermarket.sh > ${SNIPPET_DIR}/sync_repo_supermarket.txt
echo >> ${SNIPPET_DIR}/sync_repo_supermarket.txt

source create_publication_supermarket.sh > ${SNIPPET_DIR}/create_publication_supermarket.txt
echo >> ${SNIPPET_DIR}/create_publication_supermarket.txt

source create_distribution_supermarket.sh > ${SNIPPET_DIR}/create_distribution_supermarket.txt
echo >> ${SNIPPET_DIR}/create_distribution_supermarket.txt
