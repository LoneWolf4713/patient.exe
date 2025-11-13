import { Box, Text, HStack, VStack } from "@chakra-ui/react";
import { motion } from "framer-motion";

const MotionBox = motion(Box);
const MotionText = motion(Text);





function ChatMessage({ message, isUser, isStreaming }) {
  return (
    <HStack w="100%" justify={isUser ? "flex-end" : "flex-start"}>
      <MotionBox
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        whileHover={isUser ? { x: -10 } : { x: 10 }}
        transition={{ type: "spring", stiffness: 120 }}
        maxW="70%"
        bg={isUser ? "#2F4858" : "#6E4F2F"}
        color="#e5e4dc"
        textAlign={isUser ? "right" : "left"}
        p={3}
        py={2}
        borderRadius={5}
        fontFamily="grotesk"
        boxShadow="sm"
      >
        <MotionText
          animate={{ height: "auto" }}
          transition={{ type: "spring", stiffness: 140, damping: 14 }}
        >
          {message}
          
        </MotionText>
      </MotionBox>
    </HStack>
  );
}

export default ChatMessage;
