pulp_http POST $BASE_ADDR/pulp/api/v3/remotes/cookbook/cookbook/ name='foo_remote' url='https://supermarket.chef.io/' policy=immediate cookbooks:='{"pulp": "", "qpid": "", "ubuntu": ""}'
export REMOTE_HREF=$(http $BASE_ADDR/pulp/api/v3/remotes/cookbook/cookbook/?name=foo_remote | jq -r '.results[0].pulp_href')
