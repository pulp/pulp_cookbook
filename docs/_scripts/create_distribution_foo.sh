pulp_http POST $BASE_ADDR/pulp/api/v3/distributions/cookbook/cookbook/ name='foo' base_path='foo' publication=$PUBLICATION_HREF
export DISTRIBUTION_HREF=$(http $BASE_ADDR/pulp/api/v3/distributions/cookbook/cookbook/?name=foo | jq -r '.results[0].pulp_href')
