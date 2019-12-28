package com.adim.springbootMS.services;

import com.adim.springbootMS.web.model.CustomerDto;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class CustomerServiceImpl implements CustomerService {

    @Override
    public CustomerDto getCutomerNamebyID(UUID uid) {
        return CustomerDto.builder().uid(UUID.randomUUID())
                .customerName("Aditya Mandlekar")
                .build();
    }
}
