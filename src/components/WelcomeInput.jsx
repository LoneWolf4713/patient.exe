import { Box, Input, VStack, Text, InputGroup, InputRightElement, Button } from "@chakra-ui/react";
import { useState } from "react";
import { TbArrowRight } from "react-icons/tb";

import {motion} from "framer-motion";

const MotionButton = motion(Button);
const MotionInputGroup = motion(InputGroup);

function WelcomeInput({ onStartChat }) {
  const [value, setValue] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim()) {
      onStartChat(value);
    }
  };

  return (
    <Box
      as="form"
      onSubmit={handleSubmit}
      w="100%"
      maxW="2xl"
    
    >
      <VStack align="stretch" spacing={2}>
        <Text
          fontSize="xs"
          
          textTransform="uppercase"
          letterSpacing="1px"
        >
        </Text>

        <MotionInputGroup
          whileHover={{scale: 1.1, boxShadow: "0 0 0 0px rgba(0, 0, 0, 0.15)"}}
          transition={{duration: 0.15}}
        size="lg">
        
        <Input
          placeholder="Type your first message..."
          size="lg"
          variant="flushed"
          borderBottom="1px solid"
          borderRadius={0}
          borderColor="gray.500"
          fontFamily="grotesk"

        
          
          fontSize="lg"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          _focus={{ borderColor:"#080808", boxShadow: "none" }}
        />
        <InputRightElement >
        <MotionButton type="submit"  whileHover={{scale: 1.5}} whileTap={{scale: 0.9}} size='sm' h="100%" bg="none" _hover={{ bg: "transparent" }} px={3} fontSize={20}>
          <TbArrowRight />
        </MotionButton>
      </InputRightElement>
        </MotionInputGroup>
      </VStack>
    </Box>
  );
}

export default WelcomeInput;
