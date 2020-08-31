pulp_http POST $BASE_ADDR/pulp/api/v3/distributions/cookbook/cookbook/ name='supermarket' base_path='supermarket' publication=$PUBLICATION_HREF
export DISTRIBUTION_HREF=$(http $BASE_ADDR/pulp/api/v3/distributions/cookbook/cookbook/?name=supermarket | jq -r '.results[0].pulp_href')
