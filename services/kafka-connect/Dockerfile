FROM openjdk:11-jre-slim

# Install wget and other utilities
RUN apt-get update && apt-get install -y wget curl && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/kafka

# Download Apache Kafka
RUN wget -O kafka.tgz https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz && \
    tar -xzf kafka.tgz && \
    mv kafka_2.13-3.6.0/* . && \
    rm -rf kafka_2.13-3.6.0 kafka.tgz

# Create plugins directory
RUN mkdir -p /opt/kafka/plugins/kafka-connect-jdbc

# Download PostgreSQL connector
RUN wget -O /opt/kafka/plugins/kafka-connect-jdbc/kafka-connect-jdbc.jar \
    https://packages.confluent.io/maven/io/confluent/kafka-connect-jdbc/10.7.4/kafka-connect-jdbc-10.7.4.jar

# Download PostgreSQL JDBC driver
RUN wget -O /opt/kafka/plugins/kafka-connect-jdbc/postgresql-jdbc.jar \
    https://jdbc.postgresql.org/download/postgresql-42.6.0.jar

# Copy configuration
COPY connect-distributed.properties /opt/kafka/config/

# Expose port
EXPOSE 8083

# Start Kafka Connect
CMD ["/opt/kafka/bin/connect-distributed.sh", "/opt/kafka/config/connect-distributed.properties"]
