# Interview Preparation Guide - Java, Spring, Databases, Docker & Kubernetes

**Purpose:** Reinforce core knowledge for senior/staff engineer interviews
**Focus Areas:** Java, Spring Framework, Databases (MySQL, MongoDB, Redis), Docker, Kubernetes

---

## Table of Contents
1. [Java Core Concepts](#java-core-concepts)
2. [Spring Framework](#spring-framework)
3. [Database Concepts](#database-concepts)
4. [Docker](#docker)
5. [Kubernetes](#kubernetes)
6. [System Design Questions](#system-design-questions)
7. [Behavioral & Architecture Questions](#behavioral--architecture-questions)

---

## Java Core Concepts

### Memory Management & Garbage Collection

**Q: Explain Java memory structure (Heap, Stack, Metaspace)**
- **Stack:** Thread-local, stores method frames, local variables, references
- **Heap:** Shared, stores objects and instance variables
  - Young Generation (Eden + Survivor spaces)
  - Old Generation (Tenured)
- **Metaspace:** Class metadata (replaced PermGen in Java 8+)

**Q: Explain different GC algorithms**
- **Serial GC:** Single-threaded, small applications
- **Parallel GC:** Multi-threaded, throughput-focused
- **CMS (Concurrent Mark Sweep):** Low-latency, deprecated in Java 14
- **G1GC:** Default since Java 9, balanced throughput/latency
- **ZGC/Shenandoah:** Ultra-low latency (<10ms pauses), large heaps

**Q: How do you diagnose memory leaks?**
- Heap dumps (jmap, VisualVM)
- Memory profiling (JProfiler, YourKit)
- GC logs analysis
- Common causes: unclosed resources, static collections, event listeners

**Key flags to know:**
```bash
-Xms2g -Xmx4g                    # Heap size
-XX:+UseG1GC                      # GC algorithm
-XX:MaxGCPauseMillis=200         # GC tuning
-XX:+HeapDumpOnOutOfMemoryError  # Debugging
```

---

### Concurrency & Multithreading

**Q: Explain the Java Memory Model (JMM)**
- Visibility guarantees (happens-before relationship)
- volatile, synchronized, final semantics
- Thread-local caches vs main memory

**Q: What's the difference between synchronized and ReentrantLock?**
- **synchronized:** Built-in, implicit lock/unlock, limited features
- **ReentrantLock:** Explicit, tryLock(), timed locks, fairness policy, interruptible

**Q: Explain CompletableFuture and its use cases**
```java
CompletableFuture.supplyAsync(() -> fetchUser())
    .thenCompose(user -> fetchOrders(user.getId()))
    .thenApply(orders -> calculateTotal(orders))
    .exceptionally(ex -> handleError(ex));
```
- Non-blocking async operations
- Composable pipelines
- Exception handling

**Q: What's the difference between CountDownLatch, CyclicBarrier, and Semaphore?**
- **CountDownLatch:** One-time coordination, threads wait until count reaches 0
- **CyclicBarrier:** Reusable, threads wait for each other at barrier point
- **Semaphore:** Limit concurrent access to resource (permits)

**Q: Explain ThreadLocal and its pitfalls**
- Thread-confined variables
- Use case: User context, transaction IDs
- **Pitfall:** Memory leaks in thread pools (threads reused, ThreadLocal not cleared)

**Common Patterns:**
- Fork/Join Framework (parallel processing)
- Executor framework (thread pools)
- CompletionService (process results as they complete)

---

### Collections & Data Structures

**Q: HashMap internals - how does it work?**
- Array of buckets (default 16)
- Hash function determines bucket
- Collisions: Linked list → Tree (Java 8+, if > 8 elements)
- Load factor 0.75, resizes when threshold exceeded

**Q: ConcurrentHashMap vs Hashtable vs synchronized Map**
- **Hashtable:** All methods synchronized (single lock, slow)
- **Collections.synchronizedMap:** Wrapper, single lock
- **ConcurrentHashMap:** Segment/bucket-level locking, better concurrency
  - Java 8+: CAS operations, lock-free reads

**Q: When to use which collection?**
- **ArrayList vs LinkedList:** Random access vs frequent insertions/deletions
- **HashSet vs TreeSet:** No order vs sorted order (O(1) vs O(log n))
- **HashMap vs TreeMap:** Unordered vs sorted by key
- **ArrayDeque vs LinkedList:** Prefer ArrayDeque for queue/stack (better performance)

**Q: What's the difference between fail-fast and fail-safe iterators?**
- **Fail-fast:** Throw ConcurrentModificationException (ArrayList, HashMap)
- **Fail-safe:** Work on copy, don't throw (CopyOnWriteArrayList, ConcurrentHashMap)

---

### Modern Java Features (Java 8+)

**Q: Explain functional interfaces and method references**
```java
// Functional interface
@FunctionalInterface
interface Processor { String process(String input); }

// Lambda
Processor p = s -> s.toUpperCase();

// Method reference
Processor p = String::toUpperCase;
```

**Q: Stream API - intermediate vs terminal operations**
- **Intermediate:** lazy, return Stream (map, filter, flatMap)
- **Terminal:** trigger execution (collect, forEach, reduce)
```java
list.stream()
    .filter(x -> x > 10)     // Intermediate
    .map(x -> x * 2)         // Intermediate
    .collect(Collectors.toList()); // Terminal
```

**Q: Optional - when and how to use it?**
```java
// Good
Optional<User> user = findUser(id);
user.ifPresent(u -> sendEmail(u));
String name = user.map(User::getName).orElse("Unknown");

// Bad - avoid
if (user.isPresent()) { user.get()... } // Defeats purpose
```

**Q: What's new in recent Java versions?**
- **Java 11:** HttpClient, String methods, var in lambdas
- **Java 14:** Records (preview), switch expressions
- **Java 15-16:** Sealed classes, pattern matching
- **Java 17 (LTS):** Records, sealed classes, pattern matching (finalized)
- **Java 21 (LTS):** Virtual threads, pattern matching for switch

**Q: Explain Virtual Threads (Project Loom)**
- Lightweight threads (thousands/millions possible)
- Managed by JVM, not OS
- Simplifies concurrent code (write blocking code, scales like async)
```java
Thread.startVirtualThread(() -> handleRequest());
```

---

### Design Patterns

**Q: Singleton pattern - how to implement thread-safe?**
```java
// Enum (preferred)
public enum Singleton { INSTANCE; }

// Double-checked locking
private volatile static Singleton instance;
public static Singleton getInstance() {
    if (instance == null) {
        synchronized (Singleton.class) {
            if (instance == null) {
                instance = new Singleton();
            }
        }
    }
    return instance;
}
```

**Q: Factory vs Abstract Factory vs Builder**
- **Factory:** Create objects without specifying exact class
- **Abstract Factory:** Family of related objects
- **Builder:** Construct complex objects step by step (immutable objects)

**Q: Strategy vs Template Method**
- **Strategy:** Composition, algorithm selected at runtime
- **Template Method:** Inheritance, skeleton in superclass, steps in subclass

---

## Spring Framework

### Core Concepts

**Q: Explain Dependency Injection (DI) and Inversion of Control (IoC)**
- **IoC:** Framework controls object creation and lifecycle
- **DI:** Dependencies injected by framework, not created by class
- **Benefits:** Loose coupling, testability, flexibility

**Q: What are the different ways to configure beans?**
```java
// 1. XML (legacy)
<bean id="userService" class="com.example.UserService"/>

// 2. Annotations
@Component
@Service
@Repository
@Controller

// 3. Java Config (preferred)
@Configuration
public class AppConfig {
    @Bean
    public UserService userService() {
        return new UserService();
    }
}
```

**Q: Bean scopes - explain each**
- **Singleton:** One instance per Spring container (default)
- **Prototype:** New instance every time
- **Request:** One per HTTP request (web apps)
- **Session:** One per HTTP session
- **Application:** One per ServletContext

**Q: Bean lifecycle and hooks**
```java
@Component
public class MyBean {
    @PostConstruct
    public void init() { /* after properties set */ }

    @PreDestroy
    public void cleanup() { /* before destruction */ }
}
```
Order: Constructor → @Autowired → @PostConstruct → ... → @PreDestroy

**Q: @Autowired vs @Resource vs @Inject**
- **@Autowired:** Spring-specific, by-type, can use @Qualifier
- **@Resource:** Java standard, by-name (JSR-250)
- **@Inject:** Java standard, by-type (JSR-330)

**Q: How does Spring resolve circular dependencies?**
- Three-level cache for singletons
- Early exposure of partially constructed beans
- **Limitation:** Doesn't work with constructor injection + prototype scope

---

### Spring Boot

**Q: What is Spring Boot and its advantages?**
- Opinionated defaults (convention over configuration)
- Embedded servers (Tomcat, Jetty, Undertow)
- Auto-configuration based on classpath
- Production-ready features (actuator, metrics)

**Q: Explain auto-configuration - how does it work?**
- `@EnableAutoConfiguration` triggers it
- Reads `META-INF/spring.factories`
- Conditional beans (`@ConditionalOnClass`, `@ConditionalOnMissingBean`)
- Can override with custom configuration

**Q: Application.properties vs application.yml - profiles**
```yaml
# application.yml
spring:
  profiles:
    active: dev
---
spring:
  config:
    activate:
      on-profile: dev
  datasource:
    url: jdbc:mysql://localhost:3306/devdb
---
spring:
  config:
    activate:
      on-profile: prod
  datasource:
    url: jdbc:mysql://prodserver:3306/proddb
```

**Q: What is Spring Boot Actuator?**
- Production monitoring and management
- Endpoints: /health, /metrics, /info, /env
- Can expose custom metrics
- Security considerations (don't expose everything in prod)

**Q: How do you externalize configuration?**
1. application.properties/yml
2. Environment variables
3. Command-line arguments
4. Config server (Spring Cloud Config)
5. HashiCorp Vault, AWS Secrets Manager

**Priority order:** Command-line > OS env > Profile-specific files > Default files

---

### Spring Data JPA

**Q: Explain the repository pattern in Spring Data**
```java
public interface UserRepository extends JpaRepository<User, Long> {
    List<User> findByLastName(String lastName);

    @Query("SELECT u FROM User u WHERE u.email = ?1")
    User findByEmail(String email);

    @Query(value = "SELECT * FROM users WHERE status = :status",
           nativeQuery = true)
    List<User> findByStatus(@Param("status") String status);
}
```

**Q: What's the difference between JpaRepository, CrudRepository, PagingAndSortingRepository?**
- **CrudRepository:** Basic CRUD operations
- **PagingAndSortingRepository:** + Pagination and sorting
- **JpaRepository:** + Batch operations (flush, saveAllAndFlush, deleteInBatch)

**Q: Explain N+1 query problem and solutions**
```java
// Problem: Lazy loading causes N+1 queries
List<User> users = userRepo.findAll(); // 1 query
for (User u : users) {
    u.getOrders().size(); // N queries
}

// Solution 1: @EntityGraph
@EntityGraph(attributePaths = {"orders"})
List<User> findAll();

// Solution 2: JOIN FETCH
@Query("SELECT u FROM User u JOIN FETCH u.orders")
List<User> findAllWithOrders();

// Solution 3: Batch fetching
@BatchSize(size = 10)
```

**Q: @Transactional - explain propagation and isolation**
```java
@Transactional(
    propagation = Propagation.REQUIRED,
    isolation = Isolation.READ_COMMITTED,
    timeout = 30,
    rollbackFor = Exception.class
)
```
- **Propagation:** REQUIRED, REQUIRES_NEW, NESTED, SUPPORTS, MANDATORY, NEVER, NOT_SUPPORTED
- **Isolation:** DEFAULT, READ_UNCOMMITTED, READ_COMMITTED, REPEATABLE_READ, SERIALIZABLE

**Q: When does @Transactional not work?**
- Private methods (proxy can't intercept)
- Internal method calls (this.method() - proxy bypassed)
- Not called through Spring proxy
- Exception caught and not re-thrown

---

### Spring MVC / REST

**Q: Explain the request lifecycle in Spring MVC**
1. DispatcherServlet receives request
2. HandlerMapping finds controller
3. HandlerAdapter invokes controller method
4. Controller returns ModelAndView (or @ResponseBody)
5. ViewResolver resolves view (if not REST)
6. View renders response

**Q: @RestController vs @Controller**
```java
@Controller
public class WebController {
    @GetMapping("/page")
    public String page(Model model) {
        return "viewName"; // Returns view name
    }
}

@RestController // = @Controller + @ResponseBody on all methods
public class ApiController {
    @GetMapping("/api/data")
    public Data getData() {
        return data; // Returns serialized object
    }
}
```

**Q: Exception handling in Spring**
```java
// Global handler
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(UserNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(UserNotFoundException ex) {
        return new ErrorResponse(ex.getMessage());
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleGeneral(Exception ex) {
        return new ErrorResponse("Internal error");
    }
}

// Controller-specific
@ExceptionHandler(ValidationException.class)
public ResponseEntity<ErrorResponse> handleValidation(ValidationException ex) {
    return ResponseEntity.badRequest().body(new ErrorResponse(ex.getMessage()));
}
```

**Q: How do you validate request bodies?**
```java
@PostMapping("/users")
public ResponseEntity<User> createUser(@Valid @RequestBody UserDTO dto) {
    // @Valid triggers validation
}

public class UserDTO {
    @NotNull
    @Size(min = 2, max = 50)
    private String name;

    @Email
    private String email;

    @Min(18)
    private Integer age;
}
```

**Q: Content negotiation - how does it work?**
- Request header: `Accept: application/json` or `Accept: application/xml`
- Spring selects appropriate HttpMessageConverter
- Can configure with `produces` attribute: `@GetMapping(produces = "application/json")`

---

### Spring Security

**Q: Explain authentication vs authorization**
- **Authentication:** Who are you? (login, verify credentials)
- **Authorization:** What can you do? (permissions, roles)

**Q: How does Spring Security filter chain work?**
```
Request → SecurityFilterChain → Application
           ↓
         Multiple filters:
         - UsernamePasswordAuthenticationFilter
         - JwtAuthenticationFilter
         - ExceptionTranslationFilter
         - FilterSecurityInterceptor
```

**Q: Basic configuration example**
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

**Q: JWT authentication - how to implement?**
```java
// Filter to validate JWT
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) {
        String token = extractToken(request);
        if (token != null && jwtUtil.validateToken(token)) {
            UserDetails user = jwtUtil.getUserFromToken(token);
            UsernamePasswordAuthenticationToken auth =
                new UsernamePasswordAuthenticationToken(user, null, user.getAuthorities());
            SecurityContextHolder.getContext().setAuthentication(auth);
        }
        chain.doFilter(request, response);
    }
}
```

**Q: Method-level security**
```java
@EnableMethodSecurity
@Configuration
public class MethodSecurityConfig {}

@Service
public class UserService {
    @PreAuthorize("hasRole('ADMIN')")
    public void deleteUser(Long id) {}

    @PreAuthorize("#userId == authentication.principal.id")
    public User getUser(Long userId) {}

    @PostAuthorize("returnObject.owner == authentication.principal.username")
    public Document getDocument(Long id) {}
}
```

---

### Spring Reactive (WebFlux)

**Q: When to use WebFlux over traditional Spring MVC?**
- **WebFlux (Reactive):** High concurrency, non-blocking I/O, streaming
- **Spring MVC:** Traditional CRUD, blocking I/O, simpler mental model
- **Don't use WebFlux if:** Database is blocking (most are), team unfamiliar

**Q: Mono vs Flux**
```java
Mono<User> user = userRepository.findById(id);     // 0 or 1 element
Flux<User> users = userRepository.findAll();        // 0 to N elements

// Composition
Mono<Order> order = userService.getUser(id)
    .flatMap(user -> orderService.getOrderForUser(user));

Flux<String> names = userRepository.findAll()
    .map(User::getName)
    .filter(name -> name.startsWith("A"));
```

**Q: Backpressure - what is it?**
- Consumer can't keep up with producer
- Reactive Streams protocol handles it
- Strategies: buffer, drop, error, latest

---

## Database Concepts

### SQL (MySQL/PostgreSQL)

**Q: ACID properties - explain each**
- **Atomicity:** All or nothing (transaction succeeds or fails completely)
- **Consistency:** Database remains in valid state
- **Isolation:** Concurrent transactions don't interfere
- **Durability:** Committed data persists even after system failure

**Q: Transaction isolation levels and problems they prevent**
```
Level                    | Dirty Read | Non-Repeatable Read | Phantom Read
-------------------------|------------|---------------------|-------------
READ_UNCOMMITTED         | ✗          | ✗                   | ✗
READ_COMMITTED (default) | ✓          | ✗                   | ✗
REPEATABLE_READ          | ✓          | ✓                   | ✗ (in MySQL)
SERIALIZABLE             | ✓          | ✓                   | ✓
```
- **Dirty Read:** Read uncommitted changes
- **Non-Repeatable Read:** Same query returns different results within transaction
- **Phantom Read:** New rows appear in range query

**Q: Indexes - types and when to use**
- **B-Tree (default):** Range queries, most common
- **Hash:** Equality checks only, very fast
- **Full-text:** Text search
- **Composite:** Multiple columns, order matters
```sql
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_order_user_date ON orders(user_id, order_date);
```

**Q: Explain query execution plan and how to optimize**
```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 123;
```
Look for:
- **Type:** ALL (bad, full scan), index, ref, eq_ref, const (good)
- **Rows:** Number of rows examined
- **Key:** Which index used
- **Extra:** Using filesort (bad), Using temporary (bad), Using index (good)

**Optimization tips:**
- Add indexes on WHERE, JOIN, ORDER BY columns
- Avoid SELECT *, retrieve only needed columns
- Use LIMIT for pagination
- Avoid functions on indexed columns: `WHERE YEAR(date) = 2024` → `WHERE date >= '2024-01-01'`

**Q: Normalization - explain 1NF, 2NF, 3NF**
- **1NF:** Atomic values, no repeating groups
- **2NF:** 1NF + No partial dependencies on composite key
- **3NF:** 2NF + No transitive dependencies

**Q: When to denormalize?**
- Read-heavy workloads
- Avoid expensive JOINs
- Caching layer insufficient
- **Trade-off:** Faster reads, slower writes, data duplication

**Q: Optimistic vs Pessimistic locking**
```sql
-- Pessimistic (locks row)
SELECT * FROM inventory WHERE id = 1 FOR UPDATE;

-- Optimistic (version check)
UPDATE inventory SET quantity = 99, version = 2
WHERE id = 1 AND version = 1;
```

**Q: Explain database replication and sharding**
- **Replication:**
  - Master-slave (write to master, read from slaves)
  - Master-master (both can write, conflict resolution needed)
- **Sharding:**
  - Horizontal partitioning by key (e.g., user_id % 10)
  - Each shard is independent database
  - **Challenge:** Cross-shard queries, rebalancing

**Q: Connection pooling - why and how?**
- Creating connections is expensive
- Pool maintains ready connections
- HikariCP (Spring Boot default), C3P0, DBCP
```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
```

---

### NoSQL (MongoDB)

**Q: When to use MongoDB vs relational database?**
- **MongoDB:** Flexible schema, document-oriented, horizontal scaling, nested data
- **Relational:** ACID transactions, complex relationships, ad-hoc queries

**Q: Document model vs relational model**
```json
// Embedded (MongoDB)
{
  "_id": "user123",
  "name": "John",
  "addresses": [
    { "street": "123 Main", "city": "NYC" },
    { "street": "456 Oak", "city": "LA" }
  ]
}

// Normalized (SQL)
users: (id, name)
addresses: (id, user_id, street, city)
```

**Q: Indexes in MongoDB**
- Single field: `db.users.createIndex({ email: 1 })`
- Compound: `db.orders.createIndex({ userId: 1, date: -1 })`
- Text: `db.articles.createIndex({ content: "text" })`
- Geospatial: `db.places.createIndex({ location: "2dsphere" })`

**Q: Aggregation pipeline**
```javascript
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $group: {
      _id: "$userId",
      total: { $sum: "$amount" }
  }},
  { $sort: { total: -1 } },
  { $limit: 10 }
])
```

**Q: Sharding in MongoDB**
- Shard key determines data distribution
- Range-based or hash-based
- Config servers store metadata
- Mongos routes queries to correct shard

**Q: Replication in MongoDB**
- Replica set: Primary + secondaries
- Automatic failover
- Read preference: primary, primaryPreferred, secondary, nearest

**Q: Transactions in MongoDB**
- Multi-document ACID transactions (MongoDB 4.0+)
- Performance overhead, use only when necessary
```javascript
session.startTransaction();
try {
  db.accounts.updateOne({ _id: 1 }, { $inc: { balance: -100 } }, { session });
  db.accounts.updateOne({ _id: 2 }, { $inc: { balance: 100 } }, { session });
  session.commitTransaction();
} catch (e) {
  session.abortTransaction();
}
```

---

### Caching (Redis)

**Q: What is Redis and its use cases?**
- In-memory key-value store
- **Use cases:** Caching, session storage, pub/sub, rate limiting, leaderboards, queues

**Q: Redis data types**
- **String:** Simple key-value
- **Hash:** Object with fields (like Java Map)
- **List:** Ordered collection (queue, stack)
- **Set:** Unordered unique elements
- **Sorted Set:** Set with scores (leaderboards)
- **Bitmap, HyperLogLog, Streams**

**Q: Caching strategies**
```java
// Cache-Aside (Lazy Loading)
public User getUser(Long id) {
    User user = redis.get("user:" + id);
    if (user == null) {
        user = database.findById(id);
        redis.set("user:" + id, user, TTL);
    }
    return user;
}

// Write-Through
public void updateUser(User user) {
    database.save(user);
    redis.set("user:" + user.getId(), user, TTL);
}

// Write-Behind (Write-Back)
public void updateUser(User user) {
    redis.set("user:" + user.getId(), user, TTL);
    asyncQueue.add(() -> database.save(user));
}
```

**Q: Cache invalidation strategies**
- **TTL (Time-To-Live):** Auto-expire
- **Manual invalidation:** Delete on update
- **Event-driven:** Pub/sub notifications
- **Cache warming:** Pre-populate on startup

**Q: Redis persistence - RDB vs AOF**
- **RDB (snapshot):** Point-in-time dumps, compact, fast restart
- **AOF (append-only file):** Logs every write, more durable, larger file
- Can use both together

**Q: Redis cluster vs Sentinel**
- **Sentinel:** High availability, monitors Redis instances, automatic failover
- **Cluster:** Sharding + replication, scale horizontally, 16384 hash slots

**Q: Common pitfalls**
- Cache stampede (multiple requests miss, hit DB simultaneously)
  - Solution: Locking, probabilistic early expiration
- Memory management (maxmemory policy: allkeys-lru, volatile-lru, noeviction)
- Hot keys (distribute load, use local cache)

---

## Docker

### Core Concepts

**Q: What is Docker and why use it?**
- Containerization platform
- **Benefits:** Consistency across environments, isolation, resource efficiency, fast deployment

**Q: Container vs VM**
```
VM:      App → Guest OS → Hypervisor → Host OS → Hardware
Container: App → Container Runtime → Host OS → Hardware
```
- Containers share OS kernel, lighter and faster
- VMs fully isolated with own OS

**Q: Dockerfile best practices**
```dockerfile
# Use specific version, not 'latest'
FROM eclipse-temurin:17-jre-alpine

# Non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Multi-stage builds (smaller images)
FROM maven:3.8-openjdk-17 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:17-jre-alpine
COPY --from=build /app/target/app.jar /app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]

# Layer caching optimization
# Copy dependencies first (changes less often)
# Copy source code last (changes frequently)

# Use .dockerignore
# target/
# .git/
# *.md
```

**Q: Explain Docker layers and caching**
- Each instruction creates a layer
- Layers are cached and reused
- Order matters: Put changing instructions last
- `docker history <image>` shows layers

**Q: Docker networking modes**
- **Bridge (default):** Private network, containers can communicate
- **Host:** Share host network stack, no isolation
- **None:** No networking
- **Overlay:** Multi-host networking (Swarm/K8s)
- **Macvlan:** Assign MAC address to container

**Q: Docker volumes vs bind mounts**
```bash
# Volume (managed by Docker)
docker run -v myvolume:/data app

# Bind mount (host directory)
docker run -v /host/path:/container/path app

# tmpfs (memory, temporary)
docker run --tmpfs /tmp app
```
- **Volumes:** Preferred, Docker manages, easier backup
- **Bind mounts:** Development (live code reload)

**Q: Health checks**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8080/actuator/health || exit 1
```

**Q: Resource limits**
```bash
docker run --memory="512m" --cpus="1.5" app
```

**Q: Docker Compose - when to use?**
- Multi-container applications
- Development environments
- Simple orchestration (not production-grade like K8s)
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DB_HOST=db
    depends_on:
      - db
  db:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: secret
    volumes:
      - db-data:/var/lib/mysql
volumes:
  db-data:
```

**Q: Security best practices**
- Don't run as root
- Use minimal base images (alpine, distroless)
- Scan images for vulnerabilities (Trivy, Snyk)
- Don't include secrets in images (use secrets management)
- Keep images updated
- Use official images from trusted sources

---

## Kubernetes

### Core Concepts

**Q: What is Kubernetes and its benefits?**
- Container orchestration platform
- **Benefits:** Auto-scaling, self-healing, rolling updates, service discovery, load balancing

**Q: Kubernetes architecture - explain components**
```
Control Plane:
- API Server: Entry point, REST API
- Scheduler: Assigns pods to nodes
- Controller Manager: Maintains desired state
- etcd: Distributed key-value store (cluster state)

Worker Nodes:
- Kubelet: Manages containers on node
- Kube-proxy: Network proxy, load balancing
- Container Runtime: Docker, containerd, CRI-O
```

**Q: Explain Pods**
- Smallest deployable unit
- One or more containers (usually one)
- Share network namespace (localhost communication)
- Share volumes
- Ephemeral (not durable)

**Q: ReplicaSet vs Deployment**
- **ReplicaSet:** Maintains desired number of pod replicas
- **Deployment:** Higher-level, manages ReplicaSets
  - Rolling updates
  - Rollback capability
  - Version history
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: myapp:1.0
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
```

**Q: Services - types and when to use each**
```yaml
# ClusterIP (default) - internal only
kind: Service
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
    - port: 80
      targetPort: 8080

# NodePort - exposes on each node's IP
type: NodePort
ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080  # 30000-32767

# LoadBalancer - cloud load balancer
type: LoadBalancer

# ExternalName - DNS CNAME
type: ExternalName
externalName: external-service.example.com
```

**Q: Ingress vs Service**
- **Service:** L4 (TCP/UDP) load balancing
- **Ingress:** L7 (HTTP/HTTPS) routing, SSL termination, path-based routing
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
```

**Q: ConfigMaps vs Secrets**
```yaml
# ConfigMap - non-sensitive config
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  app.properties: |
    server.port=8080
    app.name=MyApp

# Secret - sensitive data (base64 encoded)
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  password: cGFzc3dvcmQxMjM=  # base64 encoded
stringData:
  username: admin  # plain text, auto-encoded
```
**Usage:**
```yaml
containers:
- name: app
  env:
    - name: APP_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: server.port
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secret
          key: password
  volumeMounts:
    - name: config
      mountPath: /config
volumes:
  - name: config
    configMap:
      name: app-config
```

**Q: StatefulSet vs Deployment**
- **Deployment:** Stateless apps, pods interchangeable
- **StatefulSet:** Stateful apps (databases), stable network identity, ordered deployment
  - Each pod gets stable hostname: `pod-0`, `pod-1`, `pod-2`
  - Persistent volumes bound to specific pods

**Q: DaemonSet - what is it?**
- Ensures pod runs on all (or selected) nodes
- Use cases: Log collectors, monitoring agents, node-level services
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: log-collector
spec:
  selector:
    matchLabels:
      name: log-collector
  template:
    metadata:
      labels:
        name: log-collector
    spec:
      containers:
      - name: fluentd
        image: fluentd:latest
```

**Q: Jobs vs CronJobs**
```yaml
# Job - run to completion
apiVersion: batch/v1
kind: Job
spec:
  completions: 3
  parallelism: 2
  template:
    spec:
      containers:
      - name: worker
        image: worker:latest
      restartPolicy: OnFailure

# CronJob - scheduled jobs
apiVersion: batch/v1
kind: CronJob
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup:latest
          restartPolicy: OnFailure
```

---

### Advanced Kubernetes

**Q: Resource requests vs limits**
```yaml
resources:
  requests:
    memory: "256Mi"  # Guaranteed, used for scheduling
    cpu: "500m"      # 0.5 CPU cores
  limits:
    memory: "512Mi"  # Hard limit, pod killed if exceeded (OOMKilled)
    cpu: "1000m"     # Throttled if exceeded
```
- **Requests:** Minimum guaranteed, scheduler uses for placement
- **Limits:** Maximum allowed

**Q: Explain QoS classes**
- **Guaranteed:** Requests = Limits for all containers
- **Burstable:** Requests < Limits
- **BestEffort:** No requests/limits set
Priority: Guaranteed > Burstable > BestEffort (eviction order)

**Q: Horizontal Pod Autoscaler (HPA)**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Q: Liveness vs Readiness vs Startup probes**
```yaml
livenessProbe:  # Restart if fails
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:  # Remove from service if fails
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5

startupProbe:  # For slow-starting apps
  httpGet:
    path: /startup
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

**Q: Rolling updates and rollback**
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Max pods above desired during update
    maxUnavailable: 0  # Max pods unavailable during update
```
```bash
kubectl rollout status deployment/app
kubectl rollout history deployment/app
kubectl rollout undo deployment/app
kubectl rollout undo deployment/app --to-revision=2
```

**Q: Namespaces - when and why?**
- Logical isolation (dev, staging, prod)
- Resource quotas per namespace
- RBAC per namespace
- Multiple teams/projects
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
```

**Q: PersistentVolumes and PersistentVolumeClaims**
```yaml
# PV - storage resource
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-data
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: fast
  hostPath:
    path: /mnt/data

# PVC - request for storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: fast
```
**Access Modes:**
- **ReadWriteOnce (RWO):** Single node
- **ReadOnlyMany (ROX):** Multiple nodes, read-only
- **ReadWriteMany (RWX):** Multiple nodes, read-write

**Q: Helm - what is it and why use it?**
- Package manager for K8s
- Templating for YAML files
- Versioning and rollback
- Reusable charts
```bash
helm install myapp ./mychart
helm upgrade myapp ./mychart
helm rollback myapp 1
helm uninstall myapp
```

**Q: Service Mesh (Istio/Linkerd) - basics**
- Traffic management (routing, load balancing)
- Security (mTLS, authentication)
- Observability (tracing, metrics)
- Sidecar proxy pattern (Envoy)

**Q: Network Policies**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

**Q: RBAC (Role-Based Access Control)**
```yaml
# Role - namespace-scoped
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]

# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

**Q: Common troubleshooting commands**
```bash
# Pods
kubectl get pods
kubectl describe pod <name>
kubectl logs <pod> [-f] [--previous]
kubectl exec -it <pod> -- /bin/sh

# Deployments
kubectl get deployments
kubectl describe deployment <name>
kubectl rollout status deployment/<name>

# Services
kubectl get svc
kubectl describe svc <name>
kubectl get endpoints <service>

# Events
kubectl get events --sort-by=.metadata.creationTimestamp

# Resource usage
kubectl top nodes
kubectl top pods

# Debug
kubectl run debug --image=busybox --rm -it -- /bin/sh
kubectl port-forward <pod> 8080:8080
```

---

## System Design Questions

### Common Patterns

**Q: Design a scalable REST API**
```
Components:
- Load Balancer (AWS ALB, NGINX)
- API Gateway (rate limiting, auth)
- Application Servers (stateless, multiple instances)
- Cache Layer (Redis)
- Database (Primary + Replicas)
- Message Queue (for async tasks)
- CDN (static content)

Considerations:
- Horizontal scaling (add more servers)
- Caching strategy
- Database indexing and query optimization
- Monitoring and logging
- Security (authentication, rate limiting)
```

**Q: How do you handle rate limiting?**
```java
// Token bucket algorithm
public class RateLimiter {
    private final int capacity;
    private final int refillRate;
    private int tokens;
    private long lastRefill;

    public synchronized boolean allowRequest() {
        refill();
        if (tokens > 0) {
            tokens--;
            return true;
        }
        return false;
    }

    private void refill() {
        long now = System.currentTimeMillis();
        long elapsed = now - lastRefill;
        int tokensToAdd = (int) (elapsed * refillRate / 1000);
        tokens = Math.min(capacity, tokens + tokensToAdd);
        lastRefill = now;
    }
}

// Using Redis (distributed)
String key = "rate_limit:" + userId;
long count = redis.incr(key);
if (count == 1) {
    redis.expire(key, 60); // 1 minute window
}
return count <= 100; // Max 100 requests per minute
```

**Q: Design a distributed cache**
```
Requirements:
- High availability
- Low latency
- Consistent hashing for distribution
- Replication for redundancy

Implementation:
- Redis Cluster or Memcached
- Consistent hashing ring
- Replication factor (2-3 replicas)
- TTL for cache eviction
- Cache warming strategy

Challenges:
- Cache invalidation
- Cache stampede
- Thundering herd problem
```

**Q: How do you ensure idempotency in distributed systems?**
```java
// Idempotency key
@PostMapping("/orders")
public ResponseEntity<?> createOrder(
    @RequestHeader("Idempotency-Key") String key,
    @RequestBody OrderRequest request) {

    // Check if already processed
    Order existing = orderRepository.findByIdempotencyKey(key);
    if (existing != null) {
        return ResponseEntity.ok(existing);
    }

    // Process order
    Order order = orderService.create(request);
    order.setIdempotencyKey(key);
    orderRepository.save(order);

    return ResponseEntity.ok(order);
}
```

**Q: Circuit breaker pattern**
```java
@Service
public class ExternalService {
    private final CircuitBreaker circuitBreaker;

    public String callExternal() {
        return circuitBreaker.executeSupplier(() -> {
            return restTemplate.getForObject("http://external/api", String.class);
        });
    }
}

// Config
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)
    .waitDurationInOpenState(Duration.ofSeconds(30))
    .slidingWindowSize(10)
    .build();
```

**Q: Event-driven architecture with Kafka**
```
Producer → Kafka Topic → Consumer Groups

Patterns:
- Event Sourcing (store events, not state)
- CQRS (separate read/write models)
- Saga pattern (distributed transactions)

Example: Order processing
1. Order created → OrderCreated event
2. Payment service consumes → processes payment
3. Payment success → PaymentCompleted event
4. Inventory service consumes → reserves inventory
5. Shipping service consumes → schedules shipment

Benefits:
- Loose coupling
- Scalability
- Resilience
- Audit trail
```

**Q: Database scaling strategies**
```
Vertical Scaling:
- Bigger machine (CPU, RAM)
- Easier, limited ceiling

Horizontal Scaling:
1. Read Replicas
   - Master for writes, replicas for reads
   - Replication lag consideration

2. Sharding
   - Partition data across databases
   - Shard key selection critical
   - Cross-shard queries challenging

3. CQRS
   - Separate read and write databases
   - Write to normalized DB
   - Replicate to denormalized read DB
```

---

## Behavioral & Architecture Questions

**Q: Describe a time you optimized application performance**
Template answer:
- **Situation:** Describe the performance issue
- **Metrics:** What was slow? (response time, throughput)
- **Analysis:** How did you identify the bottleneck? (profiling, monitoring)
- **Solution:** What did you implement? (caching, indexing, async processing)
- **Result:** Quantify improvement (50% faster, 10x throughput)

**Q: How do you approach debugging a production issue?**
1. **Gather information:** Logs, metrics, error reports
2. **Isolate:** Recent deployments? Traffic spike? External dependency?
3. **Reproduce:** Can you reproduce in staging?
4. **Hypothesis:** What could cause this?
5. **Test:** Verify hypothesis
6. **Fix:** Implement solution
7. **Verify:** Monitor after deployment
8. **Postmortem:** Document and prevent recurrence

**Q: Explain your approach to system design**
1. **Clarify requirements:** Functional and non-functional (scale, latency, availability)
2. **Estimate scale:** Users, requests/sec, data volume
3. **High-level design:** Major components and interactions
4. **Deep dive:** Database schema, API design, critical components
5. **Bottlenecks:** Identify and address
6. **Trade-offs:** Discuss alternatives and rationale

**Q: How do you ensure code quality?**
- Code reviews (peer review, automated tools)
- Unit tests (JUnit, Mockito)
- Integration tests
- Static analysis (SonarQube, SpotBugs)
- CI/CD pipeline (automated testing)
- Documentation
- Design patterns and best practices

**Q: Microservices vs Monolith - when to use each?**
**Monolith:**
- Small team
- Simple domain
- Faster initial development
- Easier deployment

**Microservices:**
- Large team (multiple teams)
- Complex domain (different subdomain needs)
- Independent scaling needs
- Polyglot requirements
- **Trade-off:** Complexity (distributed systems, monitoring, deployment)

**Q: How do you handle backward compatibility when changing APIs?**
- Versioning (/api/v1, /api/v2)
- Deprecation period (announce, give time)
- Additive changes (add fields, don't remove)
- Optional parameters (default values)
- Feature flags
- Contract testing (Pact)

---

## Quick Reference - Common Commands

### Docker
```bash
docker build -t myapp:1.0 .
docker run -d -p 8080:8080 --name myapp myapp:1.0
docker exec -it myapp /bin/sh
docker logs -f myapp
docker stop myapp
docker rm myapp
docker system prune -a  # Clean up
```

### Kubernetes
```bash
kubectl apply -f deployment.yaml
kubectl get pods -o wide
kubectl describe pod <name>
kubectl logs <pod> -f
kubectl exec -it <pod> -- /bin/bash
kubectl port-forward <pod> 8080:8080
kubectl delete -f deployment.yaml
kubectl scale deployment myapp --replicas=5
```

### Git
```bash
git status
git add .
git commit -m "Message"
git push origin main
git pull --rebase
git checkout -b feature-branch
git merge feature-branch
git rebase main
git cherry-pick <commit-hash>
```

### Maven
```bash
mvn clean install
mvn test
mvn spring-boot:run
mvn dependency:tree
mvn versions:display-dependency-updates
```

---

## Interview Preparation Checklist

### Week 1-2: Core Java & Spring
- [ ] Review concurrency (locks, thread pools, CompletableFuture)
- [ ] Practice Stream API and lambdas
- [ ] Understand Spring Boot auto-configuration
- [ ] Review Spring Security (JWT, OAuth2)
- [ ] Practice exception handling patterns

### Week 3: Databases
- [ ] Review SQL optimization (indexes, query plans)
- [ ] Practice MongoDB aggregation pipelines
- [ ] Understand Redis caching strategies
- [ ] Review transaction isolation levels

### Week 4: Docker & Kubernetes
- [ ] Practice writing Dockerfiles
- [ ] Review K8s resource types (Pods, Deployments, Services)
- [ ] Understand scaling strategies (HPA, VPA)
- [ ] Practice kubectl commands

### Week 5: System Design
- [ ] Practice designing scalable APIs
- [ ] Review distributed systems patterns
- [ ] Understand CAP theorem and consistency models
- [ ] Practice back-of-the-envelope calculations

### Week 6: Mock Interviews
- [ ] Practice coding problems (LeetCode medium/hard)
- [ ] Practice system design questions
- [ ] Prepare behavioral stories (STAR format)
- [ ] Review your projects and be ready to discuss

---

## Resources

### Books
- Effective Java (Joshua Bloch)
- Spring in Action (Craig Walls)
- Designing Data-Intensive Applications (Martin Kleppmann)
- Kubernetes in Action (Marko Lukša)

### Online
- Java Memory Model (JSR 133)
- Spring documentation (spring.io)
- Kubernetes documentation (kubernetes.io)
- System Design Primer (GitHub)

### Practice
- LeetCode (algorithms)
- System Design Interview (YouTube)
- TryHackMe / HackTheBox (security)

---

*Update this document as you identify gaps or new trends in interviews.*
