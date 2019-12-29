package com.adim.springbootMS.services;

import com.adim.springbootMS.web.model.CustomerDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@Slf4j
public class CustomerServiceImpl implements CustomerService {

    @Override
    public CustomerDto getCutomerNamebyID(UUID uid) {
        return CustomerDto.builder().uid(UUID.randomUUID())
                .customerName("Aditya Mandlekar")
                .build();
    }

    @Override
    public CustomerDto saveNewcustomer(CustomerDto customerDto) {
        return CustomerDto.builder().uid(UUID.randomUUID()).build();
    }

    @Override
    public void updateCustomerbyID(UUID uuid, CustomerDto customerDto) {
        log.debug("Updated Customer..." + uuid);
    }

    @Override
    public void deleteCustomerbyID(UUID uuid) {
        log.debug("Deleted Customer..." + uuid);
    }

}
