import pickle

import sparql

if __name__ == '__main__':
    query = """
          select ?course ?code ?title where {
              ?course rdf:type schema:Course ;
                  schema:name ?title ;
                  schema:courseCode ?code .
          }
          """
    response = sparql.get(query=query)
    response['title'] = response['code'] + ': ' + response['title']
    response.drop('code', axis=1, inplace=True)
    with open('../assets/course_titles.pickle', 'wb') as file:
        pickle.dump(response, file)
    response.to_excel('../assets/course_titles.xlsx')