package guru.springframework.msscbreweryclient.web.client;

import guru.springframework.msscbreweryclient.web.model.CustomerDto;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.net.URI;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest
class CustomerClientTest {
    @Autowired
    CustomerClient customerClient;

    @Test
    void getCutomerNamebyIDtest() {
        CustomerDto customerDto=customerClient.getCutomerNamebyID(UUID.randomUUID());
        assertNotNull(customerDto);
    }

    @Test
    void saveNewCustomertest() {
        CustomerDto customerDto= CustomerDto.builder().name("Aditya Mandlekar").build();
        URI uri=customerClient.saveNewCustomer(customerDto);
        assertNotNull(uri);
        System.out.println(uri.toString());
    }

    @Test
    void updateCustomertest() {
        CustomerDto customerDto= CustomerDto.builder().name("Aditya Mandlekar").build();
        customerClient.updateCustomer(UUID.randomUUID(),customerDto);
    }

    @Test
    void deleteCustomertest() {
        customerClient.deleteCustomer(UUID.randomUUID());
    }
}