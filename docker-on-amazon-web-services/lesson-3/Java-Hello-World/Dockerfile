FROM maven:3.8.3-openjdk-17 AS maven_build
COPY . .
RUN mvn clean package -D maven.test.skip=true

FROM maven:3.8.3-openjdk-17
COPY --from=maven_build /target/demo-0.0.1-SNAPSHOT.jar /app/demo-0.0.1-SNAPSHOT.jar
EXPOSE 8080
USER 1002
ENTRYPOINT ["java", "-jar", "/app/demo-0.0.1-SNAPSHOT.jar"]
