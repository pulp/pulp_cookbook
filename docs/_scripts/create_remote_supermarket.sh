pulp_http POST $BASE_ADDR/pulp/api/v3/remotes/cookbook/cookbook/ name='supermarket' url='https://supermarket.chef.io/' policy=on_demand
export REMOTE_HREF=$(http $BASE_ADDR/pulp/api/v3/remotes/cookbook/cookbook/?name=supermarket | jq -r '.results[0].pulp_href')
