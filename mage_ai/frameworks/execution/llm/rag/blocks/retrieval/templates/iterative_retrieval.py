TEMPLATES = """
elasticsearch:
  description: 'Elasticsearch is a distributed, RESTful search and analytics engine. It has native support for vector fields, enabling approximate k-NN search on dense vectors.'
  name: 'Elasticsearch'
  path: data_loaders/iterative_retrieval/elasticsearch.py
  type: data_loader
  inputs:
    text:
      style:
        input_type: null
        multiline: true
        monospace: false
      type: text_field
    number:
      style:
        input_type: number
        multiline: false
        monospace: true
      type: text_field
  variables:
    connection_string:
      description: 'The database connection string.'
      name: 'Connection string'
      input: text
      required: true
      types:
        - string
      value: 'http://localhost:9200'
    index_name:
      description: 'The name of the Elasticsearch index where the documents will be stored.'
      name: 'Index name'
      input: text
      required: true
      types:
        - string
      value: documents
    vector_column_name:
      description: 'The name of the column that contains the vectors.'
      name: 'Vector column name'
      input: text
      required: false
      types:
        - string
      value: embedding
    chunk_column:
      description: 'The name of the column that contains the chunk text.'
      name: 'Chunk column name'
      input: text
      required: false
      types:
        - string
      value: chunk
"""